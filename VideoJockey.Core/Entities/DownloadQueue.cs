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
        /// Download status
        /// </summary>
        public DownloadStatus Status { get; set; } = DownloadStatus.Pending;

        /// <summary>
        /// Download progress percentage (0-100)
        /// </summary>
        public int Progress { get; set; } = 0;

        /// <summary>
        /// Error message if download failed
        /// </summary>
        public string? ErrorMessage { get; set; }

        /// <summary>
        /// Download started at
        /// </summary>
        public DateTime? StartedAt { get; set; }

        /// <summary>
        /// Download completed at
        /// </summary>
        public DateTime? CompletedAt { get; set; }

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
    }

    /// <summary>
    /// Download status enumeration
    /// </summary>
    public enum DownloadStatus
    {
        Pending,
        Queued,
        Downloading,
        Processing,
        Completed,
        Failed,
        Cancelled
    }
}