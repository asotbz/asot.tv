using System;

namespace VideoJockey.Core.Entities
{
    /// <summary>
    /// Represents a video download queue item
    /// </summary>
    public class DownloadQueue : BaseEntity
    {
        /// <summary>
        /// URL of the video to download
        /// </summary>
        public string Url { get; set; } = string.Empty;

        /// <summary>
        /// Title of the video (if known)
        /// </summary>
        public string? Title { get; set; }

        /// <summary>
        /// Artist name (if known)
        /// </summary>
        public string? Artist { get; set; }
        
        /// <summary>
        /// Output path for the downloaded file
        /// </summary>
        public string? OutputPath { get; set; }
        
        /// <summary>
        /// Format to download (e.g., "best", "720p", etc.)
        /// </summary>
        public string? Format { get; set; }

        /// <summary>
        /// Download status
        /// </summary>
        public string Status { get; set; } = "Pending";

        /// <summary>
        /// Download progress percentage (0-100)
        /// </summary>
        public double Progress { get; set; } = 0;

        /// <summary>
        /// Error message if download failed
        /// </summary>
        public string? ErrorMessage { get; set; }

        /// <summary>
        /// Download started at
        /// </summary>
        public DateTime? StartedDate { get; set; }

        /// <summary>
        /// Download completed at
        /// </summary>
        public DateTime? CompletedDate { get; set; }
        
        /// <summary>
        /// Date when the item was added to the queue
        /// </summary>
        public DateTime AddedDate { get; set; } = DateTime.UtcNow;
        
        /// <summary>
        /// Download speed
        /// </summary>
        public string? DownloadSpeed { get; set; }
        
        /// <summary>
        /// Estimated time of arrival
        /// </summary>
        public string? ETA { get; set; }

        /// <summary>
        /// File size in bytes (if known)
        /// </summary>
        public long? FileSize { get; set; }

        /// <summary>
        /// Downloaded file path
        /// </summary>
        public string? FilePath { get; set; }

        /// <summary>
        /// Priority (higher number = higher priority)
        /// </summary>
        public int Priority { get; set; } = 0;

        /// <summary>
        /// Number of retry attempts
        /// </summary>
        public int RetryCount { get; set; } = 0;

        /// <summary>
        /// Maximum number of retries allowed
        /// </summary>
        public int MaxRetries { get; set; } = 3;
        
        /// <summary>
        /// Soft delete flag
        /// </summary>
        public bool IsDeleted { get; set; } = false;
        
        /// <summary>
        /// Soft delete date
        /// </summary>
        public DateTime? DeletedDate { get; set; }
        
        /// <summary>
        /// Whether the item is active (legacy compatibility)
        /// </summary>
        public new bool IsActive => !IsDeleted;
    }
}