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

mean_episode_return_buf = deque(maxlen=100)


def _load_from_latest_weights(flags, learner_model, actor_models, device_iterator, map_device):
    """Load from the latest weight file and corresponding log record."""
    try:
        import pandas as pd
        import glob
        
        # Find the latest weight file
        weights_dir = os.path.join(flags.savedir, flags.xpid)
        weight_files = glob.glob(os.path.join(weights_dir, "guandan_weights_*.ckpt"))
        
        if not weight_files:
            return 0, {'mean_episode_return': 0, 'loss': 0}
        
        # Extract frame numbers from weight files
        weight_frames = []
        for wf in weight_files:
            try:
                frame_num = int(os.path.basename(wf).split('_')[-1].split('.')[0])
                weight_frames.append((frame_num, wf))
            except:
                continue
        
        if not weight_frames:
            return 0, {'mean_episode_return': 0, 'loss': 0}
        
        # Get the latest weight file
        weight_frames.sort(key=lambda x: x[0])
        max_weight_frame, max_weight_file = weight_frames[-1]
        
        log.info('Found latest weight file: %s (frame: %d)', max_weight_file, max_weight_frame)
        
        # Load the latest weight file
        try:
            weight_checkpoint = torch.load(max_weight_file, map_location=map_device, weights_only=False)
            learner_model.load_state_dict(weight_checkpoint)
            for device_id in device_iterator:
                actor_models[device_id].load_state_dict(weight_checkpoint)
            log.info('Successfully loaded weights from: %s', max_weight_file)
            
            # Find corresponding training progress from logs
            logs_file = os.path.join(flags.savedir, flags.xpid, 'logs.csv')
            if os.path.exists(logs_file):
                df = pd.read_csv(logs_file)
                if not df.empty:
                    # Ensure frames column is numeric
                    df['frames'] = pd.to_numeric(df['frames'], errors='coerce')
                    # Find log record closest to weight file frame
                    log_records = df[df['frames'] <= max_weight_frame]
                    if not log_records.empty:
                        closest_idx = log_records['frames'].idxmax()
                        frames = int(log_records['frames'].iloc[closest_idx])
                        stats = {
                            'mean_episode_return': float(log_records['mean_episode_return'].iloc[closest_idx]),
                            'loss': float(log_records['loss'].iloc[closest_idx])
                        }
                        log.info('Loaded training progress: frame=%d, stats=%s', frames, stats)
                        return frames, stats
                    else:
                        log.info('Using weight file frame: %d', max_weight_frame)
                        return max_weight_frame, {'mean_episode_return': 0, 'loss': 0}
                else:
                    log.info('Using weight file frame: %d', max_weight_frame)
                    return max_weight_frame, {'mean_episode_return': 0, 'loss': 0}
            else:
                log.info('Using weight file frame: %d', max_weight_frame)
                return max_weight_frame, {'mean_episode_return': 0, 'loss': 0}
                
        except Exception as e:
            log.warning('Failed to load weights from %s: %s', max_weight_file, e)
            return 0, {'mean_episode_return': 0, 'loss': 0}
    except Exception as e:
        log.warning('Failed to load from weight files: %s', e)
        return 0, {'mean_episode_return': 0, 'loss': 0}


def compute_loss(logits, targets):
    loss = ((logits.squeeze(-1) - targets) ** 2).mean()
    return loss


def learn(learner_model,
          batch,
          optimizer,
          flags,
          device_id
          ):
    learner_device = next(learner_model.parameters()).device

    obs_x_no_action = batch['obs_x_no_action'].to(learner_device)
    obs_action = batch['obs_action'].to(learner_device)
    obs_x = torch.cat((obs_x_no_action, obs_action), dim=2).float()
    obs_x = torch.flatten(obs_x, 0, 1)
    obs_z = torch.flatten(batch['obs_z'].to(learner_device), 0, 1).float()
    target = torch.flatten(batch['target'].to(learner_device), 0, 1)

    episode_returns = batch['episode_return'][batch['done']]
    if episode_returns.numel() > 0:
        mean_episode_return_buf.append(torch.mean(episode_returns).item())

    learner_outputs = learner_model(obs_z, obs_x, return_value=True)
    loss = compute_loss(learner_outputs['values'], target)

    stats = {
        'mean_episode_return': np.mean(list(mean_episode_return_buf)) if mean_episode_return_buf else 0.0,
        'loss': loss.item()
    }

    optimizer.zero_grad()
    loss.backward()
    nn.utils.clip_grad_norm_(learner_model.parameters(), flags.max_grad_norm)
    optimizer.step()

    return stats


def train(flags):
    if not flags.actor_device_cpu or flags.training_device != 'cpu':
        if not torch.cuda.is_available():
            raise AssertionError(
                "CUDA not available. If you have GPUs, please specify the ID after `--gpu_devices`. Otherwise, please train with CPU with `python3 train.py --actor_device_cpu --training_device cpu`")

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
        # actor and learner on same device, use num_actor_devices for available devices
        device_iterator = range(flags.num_actor_devices)
        assert flags.num_actor_devices <= len(
            flags.gpu_devices.split(',')), 'The number of actor devices can not exceed the number of available devices'

    # Determine model type
    use_transformer = flags.use_transformer and not flags.use_lstm
    
    # initialize actor models
    actor_models = {}
    for device_id in device_iterator:
        actor_model = Model(
            device=device_id, 
            use_transformer=use_transformer,
            d_model=flags.d_model,
            nhead=flags.nhead,
            num_layers=flags.num_layers,
            max_seq_len=flags.max_seq_len
        )
        actor_model.share_memory()
        actor_model.eval()
        actor_models[device_id] = actor_model

    # initialize learner model
    learner_device = flags.training_device
    if learner_device == 'cpu':
        learner_device_int = 'cpu'
    else:
        learner_device_int = int(learner_device)

    learner_model = Model(
        device=learner_device_int, 
        use_transformer=use_transformer,
        d_model=flags.d_model,
        nhead=flags.nhead,
        num_layers=flags.num_layers,
        max_seq_len=flags.max_seq_len
    )
    learner_model.train()
    # define map_location device for torch.load
    if learner_device == 'cpu':
        map_device = torch.device('cpu')
    else:
        map_device = torch.device(f'cuda:{learner_device}')

    # initialize buffer
    buffers = create_buffers(flags, device_iterator)

    # initialize queue
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

    # initialize optimizer
    optimizer = create_optimizer(flags, learner_model)

    # initialize frames and stats
    stat_keys = ['mean_episode_return', 'loss']
    frames, stats = 0, {k: 0 for k in stat_keys}

    # load model if any
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
                learner_model.train()
                try:
                    optimizer.load_state_dict(checkpoint_states['optimizer_state_dict'])
                except Exception as opt_e:
                    log.warning('Failed to load optimizer state: %s. Re-init optimizer.', opt_e)
                for device_id in device_iterator:
                    actor_models[device_id].load_state_dict(learner_model.state_dict())
                stats = checkpoint_states.get('stats', stats)
                frames = checkpoint_states.get('frames', frames)
                
                # Load from the latest weight file and corresponding log record
                frames, stats = _load_from_latest_weights(flags, learner_model, actor_models, device_iterator, map_device)
                
                log.info('Successfully loaded checkpoint. Starting from frame: %d', frames)
            except Exception as e:
                log.error('Failed to load checkpoint from %s: %r', checkpointpath, e)
                log.error('Training from scratch')
            except KeyboardInterrupt:
                log.info('The training was manually interrupted.')
                checkpoint(frames)
                return
        else:
            log.error('Checkpoint not found at %s. Training from scratch.', checkpointpath)

    # start actor processes
    actor_processes = []
    for device_id in device_iterator:
        num_actors = flags.num_actors
        for actor_id in range(num_actors):
            actor = ctx.Process(
                target=act,
                args=(actor_id, device_id, free_queue[device_id], full_queue[device_id],
                      actor_models[device_id], buffers[device_id], flags))
            actor.start()
            actor_processes.append(actor)

    def batch_and_learn(learner_id, device_id, data_lock, model_lock, stats_lock):
        nonlocal frames, stats
        while frames < flags.total_frames:
            batch = get_batch(free_queue[device_id], full_queue[device_id], buffers[device_id], flags, data_lock)
            with model_lock:
                _stats = learn(learner_model, batch, optimizer, flags, device_id)
            with stats_lock:
                for k in _stats:
                    stats[k] = _stats[k]
                to_log = dict(frames=frames)
                to_log.update({k: stats[k] for k in stat_keys})
                plogger.log(to_log)
                frames += T * B

    # initialize locks and threads
    threads = []
    data_locks = {}
    model_locks = {}
    for device_id in device_iterator:
        data_locks[device_id] = threading.Lock()
        model_locks[device_id] = threading.Lock()
    stats_lock = threading.Lock()
    learner_model_lock = threading.Lock()

    # start learner threads
    learner_device_for_threads = int(learner_device) if learner_device != 'cpu' else 'cpu'

    for device_id in device_iterator:
        if device_id == learner_device_for_threads:
            for learner_id in range(flags.num_threads):
                thread = threading.Thread(
                    target=batch_and_learn,
                    name=f'BatchAndLearn-{learner_id}',
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
        log.info('Saving checkpoint to %s', checkpointpath)
        torch.save({
            'model_state_dict': learner_model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'stats': stats,
            'flags': vars(flags),
            'frames': frames
        }, checkpointpath)

        # save the weights for evaluation purpose
        model_weights_path = os.path.join(flags.savedir, flags.xpid, f'guandan_weights_{frames}.ckpt')
        torch.save(learner_model.state_dict(), model_weights_path)

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

            if timer() - last_checkpoint_time > save_interval_seconds:
                checkpoint(frames)
                last_checkpoint_time = timer()
            end_time = timer()

            time_elapsed = end_time - start_time
            if time_elapsed > 0:
                fps = (frames - start_frames) / time_elapsed
                fps_log.append(fps)

            if len(fps_log) > 24:
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
