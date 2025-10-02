using VideoJockey.Services.Models;

namespace VideoJockey.Services.Interfaces;

public interface IDownloadSettingsProvider
{
    DownloadWorkerOptions GetOptions();
    string GetFfmpegPath();
    string GetFfprobePath();
    void Invalidate();
}
