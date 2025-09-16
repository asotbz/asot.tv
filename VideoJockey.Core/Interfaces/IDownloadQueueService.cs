using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using VideoJockey.Core.Entities;

namespace VideoJockey.Core.Interfaces
{
    public interface IDownloadQueueService
    {
        /// <summary>
        /// Adds a new download to the queue
        /// </summary>
        Task<DownloadQueue> AddToQueueAsync(string url, string? customTitle = null, int priority = 0);
        
        /// <summary>
        /// Gets all items in the queue
        /// </summary>
        Task<List<DownloadQueue>> GetQueueAsync(bool includeCompleted = false);
        
        /// <summary>
        /// Gets items pending download
        /// </summary>
        Task<List<DownloadQueue>> GetPendingDownloadsAsync();
        
        /// <summary>
        /// Updates the status of a queue item
        /// </summary>
        Task UpdateStatusAsync(int queueId, DownloadStatus status, string? errorMessage = null);
        
        /// <summary>
        /// Updates download progress
        /// </summary>
        Task UpdateProgressAsync(int queueId, double percentage, string? speed = null, string? eta = null);
        
        /// <summary>
        /// Removes an item from the queue
        /// </summary>
        Task<bool> RemoveFromQueueAsync(int queueId);
        
        /// <summary>
        /// Clears completed downloads from the queue
        /// </summary>
        Task<int> ClearCompletedAsync();
        
        /// <summary>
        /// Retries a failed download
        /// </summary>
        Task<bool> RetryDownloadAsync(int queueId);
        
        /// <summary>
        /// Gets the next item to download based on priority
        /// </summary>
        Task<DownloadQueue?> GetNextDownloadAsync();
    }
    
    public enum DownloadStatus
    {
        Pending,
        Searching,
        Downloading,
        Processing,
        Completed,
        Failed,
        Cancelled
    }
}