using VideoJockey.Core.Entities;
using VideoJockey.Services.Models;

namespace VideoJockey.Services.Interfaces;

public interface IMetadataExportService
{
    Task<MetadataExportResult> ExportVideoAsync(
        Video video,
        MetadataExportOptions options,
        CancellationToken cancellationToken = default);

    Task<IReadOnlyList<MetadataExportResult>> ExportLibraryAsync(
        IEnumerable<Video> videos,
        MetadataExportOptions options,
        CancellationToken cancellationToken = default);

    Task<MetadataExportResult> ExportArtistAsync(
        FeaturedArtist artist,
        IEnumerable<Video> videos,
        MetadataExportOptions options,
        CancellationToken cancellationToken = default);

    Task<MetadataImportResult> ImportAsync(
        string packagePath,
        CancellationToken cancellationToken = default);
}
