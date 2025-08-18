import os
import threading
import time
import timeit
import pprint
from collections import deque
import numpy as np

import torch
from torch import multiprocessing as mp
from torch import nn

from .file_writer import FileWriter
from .model import Model
from .utils import get_batch, log, create_buffers, create_optimizer, act

mean_episode_return_buf = deque(maxlen = 100)

def compute_loss(logits,targets):
    loss = ((logits.squeeze(-1) - targets)**2).mean()
    return loss

def learn(learner_model,
          batch,
          optimizer,
          flags,
          device_id
          ):
    if device_id != "cpu":
        device = torch.device(f'cuda:{device_id}')
    else:
        device = torch.device('cpu')
    obs_x_no_action = batch['obs_x_no_action'].to(device)
    obs_action = batch['obs_action'].to(device)
    obs_x = torch.cat((obs_x_no_action, obs_action), dim=2).float()
    #dim2 why ? need to check data shape
    obs_x = torch.flatten(obs_x, 0, 1)
    obs_z = torch.flatten(batch['obs_z'].to(device), 0, 1).float()

    target = torch.flatten(batch['target'].to(device), 0, 1)
    episode_returns = batch['episode_return'][batch['done']]
    if episode_returns.numel() > 0:
        mean_episode_return_buf.append(torch.mean(episode_returns).item())

    learner_outputs = learner_model(obs_z, obs_x, return_value=True)
    loss = compute_loss(learner_outputs['values'], target)

    stats = {
        'mean_episode_return':np.mean(list(mean_episode_return_buf)) if mean_episode_return_buf else 0.0,
        'loss':loss.item()
        
    }
    
    optimizer.zero_grad()
    loss.backward()
    nn.utils.clip_grad_norm_(learner_model.parameters(), flags.max_grad_norm)
    optimizer.step()

    return stats

def train(flags):
    if not flags.actor_device_cpu or flags.training_device != 'cpu':
        if not torch.cuda.is_available():
            raise AssertionError("CUDA not available. If you have GPUs, please specify the ID after `--gpu_devices`. Otherwise, please train with CPU with `python3 train.py --actor_device_cpu --training_device cpu`")
        
    plogger = FileWriter(
    xpid=flags.xpid,
    xp_args=flags.__dict__,
    rootdir=flags.savedir,
    )   
    checkpointpath = os.path.expandvars(
        os.path.expanduser('%s/%s/%s' % (flags.savedir, flags.xpid, 'model.tar')))

    T = flags.unroll_length
    B = flags.batch_size

    if flags.actor_device_cpu:
        device_iterator = ['cpu']
    else:
        #actor与learner在同一个设备上，用num_actor_devices统一表示可用设备
        device_iterator = range(flags.num_actor_devices)
        assert flags.num_actor_devices <= len(flags.gpu_devices.split(',')), 'The number of actor devices can not exceed the number of available devices'

    #initialize actor model
    actor_models = {}
    for device_id in device_iterator:
        actor_model = Model(device=device_id)
        actor_model.share_memory()
        actor_model.eval()
        actor_models[device_id] = actor_model
    
    #initialize learner model
    learner_device = device_iterator[0] if device_iterator else 'cpu'
    learner_model = Model(device = learner_device)
    # define map_location device for torch.load
    if learner_device == 'cpu':
        map_device = torch.device('cpu')
    else:
        map_device = torch.device(f'cuda:{learner_device}')
    
    #initialize buffer
    #check create_buffers
    buffers = create_buffers(flags, device_iterator) 

    #initialize queue
    ctx = mp.get_context('spawn')
    free_queue = {}
    full_queue = {}
    for device_id in device_iterator:
        _free_queue = ctx.SimpleQueue()
        for i in range(flags.num_buffers):
            _free_queue.put(i)
        _full_queue = ctx.SimpleQueue()
        free_queue[device_id] = _free_queue
        full_queue[device_id] = _full_queue
    
    #initialize optimizer(only one optimizer)
    #check create_optimizer
    optimizer = create_optimizer(flags, learner_model)

    #initialize frames and stats
    stat_keys = ['mean_episode_return','loss']
    frames, stats = 0, {k: 0 for k in stat_keys}
    

    #load model if any
    log.info('Checkpoint path: %s (exists=%s)', checkpointpath, os.path.exists(checkpointpath))
    if flags.load_model:
        if os.path.exists(checkpointpath):
            try:
                checkpoint_states = torch.load(checkpointpath, map_location=map_device, weights_only=False)
                missing, unexpected = learner_model.load_state_dict(
                    checkpoint_states['model_state_dict'], strict=False
                )
                if missing:
                    log.warning('Missing keys: %s', missing)
                if unexpected:
                    log.warning('Unexpected keys: %s', unexpected)
                try:
                    optimizer.load_state_dict(checkpoint_states['optimizer_state_dict'])
                except Exception as opt_e:
                    log.warning('Failed to load optimizer state: %s. Re-init optimizer.', opt_e)
                for device_id in device_iterator:
                    actor_models[device_id].load_state_dict(learner_model.state_dict())
                stats = checkpoint_states.get('stats', stats)
                frames = checkpoint_states.get('frames', frames)
                log.info('Successfully loaded checkpoint.')
            except Exception as e:
                log.error('Failed to load checkpoint from %s: %r', checkpointpath, e)
                log.error('Training from scratch')
            except KeyboardInterrupt:
                log.info('The training was manually interrupted.')
                checkpoint(frames)
                return
        else:
            log.error('Checkpoint not found at %s. Training from scratch.', checkpointpath)

    #starting actor and append it to actor processes
    actor_processes = []
    for device_id in device_iterator:
        num_actors = flags.num_actors 
        for actor_id in range(num_actors):

            actor = ctx.Process(
                    target=act,#need to check act function
                    args=(actor_id,device_id,free_queue[device_id], full_queue[device_id], 
                        actor_models[device_id], buffers[device_id], flags))
            actor.start()
            actor_processes.append(actor)

    def batch_and_learn(learner_id,device_id,data_lock,model_lock,stats_lock):
        #声明要修改外部变量
        nonlocal frames,stats
        while frames < flags.total_frames:
            #check get_batch 
            batch = get_batch(free_queue[device_id], full_queue[device_id], buffers[device_id], flags,data_lock)
            with model_lock:
                _stats = learn(learner_model, batch, optimizer, flags,device_id)
            with stats_lock:
                for k in _stats:
                    #update global statisis
                    stats[k] = _stats[k]
                to_log = dict(frames=frames)
                to_log.update({k: stats[k] for k in stat_keys})
                #更新日志
                plogger.log(to_log)
                frames += T * B

    #初始化锁和线程列表
    threads = []
    data_locks = {}
    model_locks = {}
    for device_id in device_iterator:
        data_locks[device_id] = threading.Lock()
        model_locks[device_id] = threading.Lock()
    stats_lock = threading.Lock()
    learner_model_lock = threading.Lock()

    #启动learner线程
    for device_id in device_iterator:
        #only one learner
        learner_id = 0
        thread = threading.Thread(
            target=batch_and_learn,
            args=(
                learner_id,
                device_id,
                data_locks[device_id],     
                learner_model_lock,    
                stats_lock              
            )
        )
        thread.start()
        threads.append(thread)

    def checkpoint(frames):
        if flags.disable_checkpoint:
            return
        log.info('Saving checkpoint to %s',checkpointpath)
        torch.save({
            'model_state_dict':learner_model.state_dict(),
            'optimizer_state_dict':optimizer.state_dict(),
            'stats':stats,
            'flags':vars(flags),
            'frames':frames           
        },checkpointpath)

        #save the weights for evaluation purpose
        model_weights_path = os.path.join(flags.savedir, flags.xpid, f'guandan_weights_{frames}.ckpt')
        torch.save(learner_model.state_dict(),model_weights_path)

    fps_log = []
    timer = timeit.default_timer

    try:
        save_interval_seconds = flags.save_interval * 60
        last_checkpoint_time = timer() - save_interval_seconds

        while frames < flags.total_frames:
            start_frames = frames
            start_time = timer()
            time.sleep(5)
            with learner_model_lock:
                learner_state_dict = learner_model.state_dict()
            for device_id in device_iterator:
                actor_models[device_id].load_state_dict(learner_state_dict)

            if timer()-last_checkpoint_time > save_interval_seconds:
                checkpoint(frames)
                last_checkpoint_time = timer()               
            end_time = timer()
            
            time_elapsed = end_time - start_time
            if time_elapsed>0:
                fps = (frames-start_frames)/time_elapsed
                fps_log.append(fps)

            if len(fps_log)>24:
                fps_log = fps_log[1:]

            fps_average = np.mean(fps_log) if fps_log else 0
            log.info(
                 'After %i frames: @ %.1f fps (avg@ %.1f fps) Stats:\n%s',
                frames,
                fps,
                fps_average,
                pprint.pformat(stats)
            )
    except KeyboardInterrupt:
        log.info('The training was manually interrupted.')
        return
    else:
        for thread in threads:
            thread.join()
        for actor in actor_processes:
            actor.join()
        log.info('Learning finished after %d frames.', frames)

    checkpoint(frames)
    plogger.close()


        




            





