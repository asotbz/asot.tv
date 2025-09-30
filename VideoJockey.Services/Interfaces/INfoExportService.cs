using VideoJockey.Core.Entities;

namespace VideoJockey.Services.Interfaces
{
    public interface INfoExportService
    {
        Task<bool> ExportNfoAsync(Video video, string outputPath);
        Task<int> BulkExportNfoAsync(IEnumerable<Video> videos, string outputDirectory, bool useVideoPath = false);
        string GenerateNfoContent(Video video);
    }
}