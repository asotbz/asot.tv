using System;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging.Abstractions;
using VideoJockey.Core.Entities;
using VideoJockey.Core.Interfaces;
using VideoJockey.Data.Context;
using VideoJockey.Data.Repositories;
using VideoJockey.Services;
using Xunit;
using DownloadStatusEnum = VideoJockey.Core.Entities.DownloadStatus;

namespace VideoJockey.Tests.Services;

public class DownloadQueueServiceTests
{
    private static (ApplicationDbContext Context, IUnitOfWork UnitOfWork, DownloadQueueService Service) CreateService()
    {
        var options = new DbContextOptionsBuilder<ApplicationDbContext>()
            .UseInMemoryDatabase(Guid.NewGuid().ToString())
            .Options;

        var context = new ApplicationDbContext(options);
        var unitOfWork = new UnitOfWork(context);
        var service = new DownloadQueueService(unitOfWork, NullLogger<DownloadQueueService>.Instance);
        return (context, unitOfWork, service);
    }

    [Fact]
    public async Task RetryFailedDownloadAsync_ResetsStatusAndIncrementsRetries()
    {
        var (context, unitOfWork, service) = CreateService();
        await using var _ = context;

        var queued = await service.AddToQueueAsync("https://example.com/test", "downloads", null, 1);
        await unitOfWork.SaveChangesAsync();

        await service.UpdateStatusAsync(queued.Id, DownloadStatusEnum.Failed, "error");
        var retryResult = await service.RetryDownloadAsync(queued.Id);

        Assert.True(retryResult);

        var updated = await service.GetByIdAsync(queued.Id);
        Assert.NotNull(updated);
        Assert.Equal(DownloadStatusEnum.Queued, updated!.Status);
        Assert.Equal(1, updated.RetryCount);
    }

    [Fact]
    public async Task GetQueuePositionAsync_UsesPriorityOrdering()
    {
        var (context, unitOfWork, service) = CreateService();
        await using var _ = context;

        var highPriority = await service.AddToQueueAsync("https://example.com/high", "downloads", null, priority: 10);
        var lowPriority = await service.AddToQueueAsync("https://example.com/low", "downloads", null, priority: 1);
        await unitOfWork.SaveChangesAsync();

        var positionHigh = await service.GetQueuePositionAsync(highPriority.Id);
        var positionLow = await service.GetQueuePositionAsync(lowPriority.Id);

        Assert.Equal(1, positionHigh);
        Assert.Equal(2, positionLow);
    }

    [Fact]
    public async Task GetPendingDownloadsAsync_ReturnsQueuedAndFailed()
    {
        var (context, unitOfWork, service) = CreateService();
        await using var _ = context;

        var queued = await service.AddToQueueAsync("https://example.com/queued", "downloads", null, priority: 1);
        var failed = await service.AddToQueueAsync("https://example.com/failed", "downloads", null, priority: 2);
        await unitOfWork.SaveChangesAsync();

        await service.UpdateStatusAsync(failed.Id, DownloadStatusEnum.Failed, "error");

        var pending = await service.GetPendingDownloadsAsync();

        Assert.Contains(pending, item => item.Id == queued.Id);
        Assert.Contains(pending, item => item.Id == failed.Id);
    }
}
