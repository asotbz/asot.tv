using System.Threading;
using System.Threading.Tasks;
using VideoJockey.Services.Models;

namespace VideoJockey.Services.Interfaces;

public interface IMetricsService
{
    Task<SystemMetrics> CaptureAsync(CancellationToken cancellationToken = default);
}
