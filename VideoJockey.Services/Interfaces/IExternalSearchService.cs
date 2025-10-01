using System.Threading;
using System.Threading.Tasks;
using VideoJockey.Services.Models;

namespace VideoJockey.Services.Interfaces;

public interface IExternalSearchService
{
    Task<ExternalSearchResult> SearchAsync(ExternalSearchQuery query, CancellationToken cancellationToken = default);
}
