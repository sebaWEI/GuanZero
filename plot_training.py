#!/usr/bin/env python3
"""
Plot training progress from logs.csv
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_training_progress():
    # Read the logs
    df = pd.read_csv('guanzero_checkpoints/guanzero/logs.csv')
    
    # Remove comment lines and convert to numeric
    df = df[~df['frames'].astype(str).str.startswith('#')]
    df['frames'] = pd.to_numeric(df['frames'], errors='coerce')
    df['mean_episode_return'] = pd.to_numeric(df['mean_episode_return'], errors='coerce')
    df['loss'] = pd.to_numeric(df['loss'], errors='coerce')
    
    # Remove rows with NaN values
    df = df.dropna()
    
    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Plot 1: Loss over frames
    ax1.plot(df['frames'], df['loss'], 'b-', linewidth=1, alpha=0.7)
    ax1.set_xlabel('Training Frames')
    ax1.set_ylabel('Loss')
    ax1.set_title('Training Loss Over Time')
    ax1.grid(True, alpha=0.3)
    
    # Add moving average for loss
    window_size = 20
    if len(df) > window_size:
        df['loss_ma'] = df['loss'].rolling(window=window_size, center=True).mean()
        ax1.plot(df['frames'], df['loss_ma'], 'r-', linewidth=2, label=f'Moving Average (window={window_size})')
        ax1.legend()
    
    # Plot 2: Episode return over frames
    ax2.plot(df['frames'], df['mean_episode_return'], 'g-', linewidth=1, alpha=0.7)
    ax2.set_xlabel('Training Frames')
    ax2.set_ylabel('Mean Episode Return')
    ax2.set_title('Mean Episode Return Over Time')
    ax2.grid(True, alpha=0.3)
    
    # Add moving average for episode return
    if len(df) > window_size:
        df['return_ma'] = df['mean_episode_return'].rolling(window=window_size, center=True).mean()
        ax2.plot(df['frames'], df['return_ma'], 'r-', linewidth=2, label=f'Moving Average (window={window_size})')
        ax2.legend()
    
    # Add horizontal line at y=0 for episode return
    ax2.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig('training_progress.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Print some statistics
    print(f"Total training frames: {df['frames'].max():,}")
    print(f"Final loss: {df['loss'].iloc[-1]:.4f}")
    print(f"Final mean episode return: {df['mean_episode_return'].iloc[-1]:.4f}")
    print(f"Best loss: {df['loss'].min():.4f}")
    print(f"Best mean episode return: {df['mean_episode_return'].max():.4f}")
    
    # Show recent progress
    print(f"\nRecent 10 steps:")
    recent = df.tail(10)
    for _, row in recent.iterrows():
        print(f"Frame {row['frames']:>8,}: Loss={row['loss']:6.3f}, Return={row['mean_episode_return']:7.3f}")

if __name__ == "__main__":
    plot_training_progress()
