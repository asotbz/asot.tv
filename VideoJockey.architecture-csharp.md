# Video Jockey C# Architecture - Self-Contained Edition

## Core Architecture Principles

### Database-Driven Configuration
All configuration, including API keys and system settings, is stored in the SQLite database and managed through the application's UI. No environment variables are required for configuration.

### Technology Decisions
- **Database**: SQLite only (via Entity Framework Core)
- **Configuration**: Stored in database, managed via admin UI
- **Deployment**: Single container with zero external configuration

## Database Schema

### Configuration Storage

```csharp
// Configuration entity stored in SQLite
public class SystemConfiguration
{
    public int Id { get; set; } = 1; // Single row
    public DateTime LastModified { get; set; }
    
    // API Keys (encrypted in database)
    public string ImvdbApiKey { get; set; }
    public string YouTubeApiKey { get; set; }
    
    // Storage Settings
    public string MediaPath { get; set; } = "/media";
    public string TempPath { get; set; } = "/data/temp";
    public long MaxStorageBytes { get; set; } = 536_870_912_000; // 500GB
    public long MaxFileSizeBytes { get; set; } = 2_147_483_648; // 2GB
    
    // Download Settings
    public int ConcurrentDownloadLimit { get; set; } = 3;
    public int RetryAttempts { get; set; } = 3;
    public string QualityPreference { get; set; } = "1080p";
    public int RateLimitMbps { get; set; } = 10;
    
    // Security Settings
    public string JwtSecret { get; set; } // Auto-generated on first run
    public int JwtExpiryMinutes { get; set; } = 15;
    public int RefreshTokenExpiryDays { get; set; } = 30;
    public int PasswordMinLength { get; set; } = 8;
    public bool RequireDigit { get; set; } = true;
    public bool RequireUppercase { get; set; } = true;
    
    // Feature Flags
    public bool EnableRegistration { get; set; } = true;
    public bool EnableGuestMode { get; set; } = false;
    public bool EnableApiDocs { get; set; } = false;
    public int MaxUsersLimit { get; set; } = 10;
    
    // System Settings
    public bool IsInitialized { get; set; } = false;
    public string AdminEmail { get; set; }
    public DateTime? LastBackup { get; set; }
}

// Encrypted field attribute for sensitive data
[AttributeUsage(AttributeTargets.Property)]
public class EncryptedAttribute : Attribute { }

// Entity Framework value converter for encryption
public class EncryptedStringConverter : ValueConverter<string, string>
{
    private readonly IDataProtector _protector;
    
    public EncryptedStringConverter(IDataProtector protector)
        : base(
            v => protector.Protect(v),
            v => protector.Unprotect(v))
    {
        _protector = protector;
    }
}
```

### Database Context

```csharp
public class VideoJockeyDbContext : DbContext
{
    private readonly IDataProtectionProvider _dataProtection;
    
    public VideoJockeyDbContext(
        DbContextOptions<VideoJockeyDbContext> options,
        IDataProtectionProvider dataProtection)
        : base(options)
    {
        _dataProtection = dataProtection;
    }
    
    public DbSet<User> Users { get; set; }
    public DbSet<Video> Videos { get; set; }
    public DbSet<QueueItem> QueueItems { get; set; }
    public DbSet<SystemConfiguration> Configuration { get; set; }
    public DbSet<AuditLog> AuditLogs { get; set; }
    
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // Configure encryption for sensitive fields
        var protector = _dataProtection.CreateProtector("VideoJockey.Encryption");
        var converter = new EncryptedStringConverter(protector);
        
        modelBuilder.Entity<SystemConfiguration>()
            .Property(e => e.ImvdbApiKey)
            .HasConversion(converter);
            
        modelBuilder.Entity<SystemConfiguration>()
            .Property(e => e.YouTubeApiKey)
            .HasConversion(converter);
            
        modelBuilder.Entity<SystemConfiguration>()
            .Property(e => e.JwtSecret)
            .HasConversion(converter);
            
        // Ensure single configuration row
        modelBuilder.Entity<SystemConfiguration>()
            .HasData(new SystemConfiguration 
            { 
                Id = 1,
                LastModified = DateTime.UtcNow,
                JwtSecret = GenerateSecureKey()
            });
    }
    
    private static string GenerateSecureKey()
    {
        using var rng = RandomNumberGenerator.Create();
        var bytes = new byte[64];
        rng.GetBytes(bytes);
        return Convert.ToBase64String(bytes);
    }
}
```

## Configuration Service

```csharp
public interface IConfigurationService
{
    Task<SystemConfiguration> GetConfigurationAsync();
    Task UpdateConfigurationAsync(SystemConfiguration config);
    Task<bool> IsSystemInitializedAsync();
    Task InitializeSystemAsync(SystemInitDto initDto);
}

public class ConfigurationService : IConfigurationService
{
    private readonly VideoJockeyDbContext _context;
    private readonly IMemoryCache _cache;
    private readonly ILogger<ConfigurationService> _logger;
    private const string CacheKey = "system_configuration";
    
    public ConfigurationService(
        VideoJockeyDbContext context,
        IMemoryCache cache,
        ILogger<ConfigurationService> logger)
    {
        _context = context;
        _cache = cache;
        _logger = logger;
    }
    
    public async Task<SystemConfiguration> GetConfigurationAsync()
    {
        return await _cache.GetOrCreateAsync(CacheKey, async entry =>
        {
            entry.SlidingExpiration = TimeSpan.FromMinutes(5);
            return await _context.Configuration
                .FirstOrDefaultAsync(c => c.Id == 1)
                ?? new SystemConfiguration();
        });
    }
    
    public async Task UpdateConfigurationAsync(SystemConfiguration config)
    {
        config.LastModified = DateTime.UtcNow;
        _context.Configuration.Update(config);
        await _context.SaveChangesAsync();
        
        // Invalidate cache
        _cache.Remove(CacheKey);
        
        _logger.LogInformation("System configuration updated");
    }
    
    public async Task<bool> IsSystemInitializedAsync()
    {
        var config = await GetConfigurationAsync();
        return config.IsInitialized;
    }
    
    public async Task InitializeSystemAsync(SystemInitDto initDto)
    {
        var config = await GetConfigurationAsync();
        
        // Create admin user
        var adminUser = new User
        {
            Id = Guid.NewGuid(),
            Email = initDto.AdminEmail,
            Username = "admin",
            PasswordHash = HashPassword(initDto.AdminPassword),
            IsAdmin = true,
            CreatedAt = DateTime.UtcNow
        };
        
        _context.Users.Add(adminUser);
        
        // Update configuration
        config.AdminEmail = initDto.AdminEmail;
        config.IsInitialized = true;
        config.ImvdbApiKey = initDto.ImvdbApiKey;
        config.YouTubeApiKey = initDto.YouTubeApiKey;
        
        await UpdateConfigurationAsync(config);
        
        _logger.LogInformation("System initialized with admin user: {Email}", 
            initDto.AdminEmail);
    }
}
```

## First-Run Setup Wizard

```razor
@page "/setup"
@layout EmptyLayout

@if (!IsInitialized)
{
    <MudContainer MaxWidth="MaxWidth.Small" Class="mt-8">
        <MudCard>
            <MudCardContent>
                <MudText Typo="Typo.h4" Class="mb-4">Welcome to Video Jockey</MudText>
                <MudText Typo="Typo.body1" Class="mb-4">
                    Let's set up your system. This wizard will only run once.
                </MudText>
                
                <MudStepper @ref="stepper">
                    <MudStep Title="Admin Account">
                        <MudTextField 
                            Label="Admin Email" 
                            @bind-Value="InitData.AdminEmail"
                            Required="true"
                            InputType="InputType.Email" />
                        <MudTextField 
                            Label="Admin Password" 
                            @bind-Value="InitData.AdminPassword"
                            Required="true"
                            InputType="InputType.Password" />
                        <MudTextField 
                            Label="Confirm Password" 
                            @bind-Value="ConfirmPassword"
                            Required="true"
                            InputType="InputType.Password" />
                    </MudStep>
                    
                    <MudStep Title="Storage Settings">
                        <MudTextField 
                            Label="Media Storage Path" 
                            @bind-Value="InitData.MediaPath"
                            HelperText="Where to store video files" />
                        <MudNumericField 
                            Label="Max Storage (GB)" 
                            @bind-Value="MaxStorageGB"
                            Min="10" Max="10000" />
                    </MudStep>
                    
                    <MudStep Title="API Keys (Optional)">
                        <MudAlert Severity="Severity.Info" Class="mb-4">
                            API keys can be added later in Settings
                        </MudAlert>
                        <MudTextField 
                            Label="IMVDb API Key" 
                            @bind-Value="InitData.ImvdbApiKey"
                            HelperText="For metadata enrichment"
                            InputType="InputType.Password" />
                        <MudTextField 
                            Label="YouTube API Key" 
                            @bind-Value="InitData.YouTubeApiKey"
                            HelperText="For video search and download"
                            InputType="InputType.Password" />
                    </MudStep>
                    
                    <MudStep Title="Complete Setup">
                        <MudText>Ready to initialize Video Jockey!</MudText>
                        <MudButton 
                            Color="Color.Primary" 
                            Variant="Variant.Filled"
                            OnClick="CompleteSetup"
                            Class="mt-4">
                            Complete Setup
                        </MudButton>
                    </MudStep>
                </MudStepper>
            </MudCardContent>
        </MudCard>
    </MudContainer>
}
else
{
    <MudContainer>
        <MudAlert Severity="Severity.Success">
            System is already initialized. Redirecting to login...
        </MudAlert>
    </MudContainer>
}

@code {
    private SystemInitDto InitData = new();
    private string ConfirmPassword;
    private int MaxStorageGB = 500;
    private MudStepper stepper;
    
    protected override async Task OnInitializedAsync()
    {
        IsInitialized = await ConfigService.IsSystemInitializedAsync();
        if (IsInitialized)
        {
            NavigationManager.NavigateTo("/login");
        }
    }
    
    private async Task CompleteSetup()
    {
        if (InitData.AdminPassword != ConfirmPassword)
        {
            Snackbar.Add("Passwords do not match", Severity.Error);
            return;
        }
        
        InitData.MaxStorageBytes = MaxStorageGB * 1_073_741_824L;
        
        await ConfigService.InitializeSystemAsync(InitData);
        NavigationManager.NavigateTo("/login");
    }
}
```

## Settings Management UI

```razor
@page "/settings"
@attribute [Authorize(Roles = "Admin")]

<MudContainer>
    <MudTabs>
        <MudTabPanel Text="General">
            <MudGrid>
                <MudItem xs="12" md="6">
                    <MudCard>
                        <MudCardContent>
                            <MudText Typo="Typo.h6">System Settings</MudText>
                            <MudSwitch 
                                @bind-Checked="Config.EnableRegistration"
                                Label="Allow User Registration" />
                            <MudSwitch 
                                @bind-Checked="Config.EnableGuestMode"
                                Label="Enable Guest Mode" />
                            <MudNumericField 
                                Label="Max Users"
                                @bind-Value="Config.MaxUsersLimit"
                                Min="1" Max="1000" />
                        </MudCardContent>
                    </MudCard>
                </MudItem>
            </MudGrid>
        </MudTabPanel>
        
        <MudTabPanel Text="API Keys">
            <MudGrid>
                <MudItem xs="12" md="6">
                    <MudCard>
                        <MudCardContent>
                            <MudText Typo="Typo.h6">External APIs</MudText>
                            <MudTextField 
                                Label="IMVDb API Key"
                                @bind-Value="Config.ImvdbApiKey"
                                InputType="InputType.Password"
                                Adornment="Adornment.End"
                                AdornmentIcon="@Icons.Material.Filled.Visibility"
                                OnAdornmentClick="ToggleImvdbVisibility" />
                            <MudTextField 
                                Label="YouTube API Key"
                                @bind-Value="Config.YouTubeApiKey"
                                InputType="InputType.Password"
                                Adornment="Adornment.End"
                                AdornmentIcon="@Icons.Material.Filled.Visibility"
                                OnAdornmentClick="ToggleYouTubeVisibility" />
                        </MudCardContent>
                    </MudCard>
                </MudItem>
            </MudGrid>
        </MudTabPanel>
        
        <MudTabPanel Text="Storage">
            <MudGrid>
                <MudItem xs="12" md="6">
                    <MudCard>
                        <MudCardContent>
                            <MudText Typo="Typo.h6">Storage Configuration</MudText>
                            <MudTextField 
                                Label="Media Path"
                                @bind-Value="Config.MediaPath"
                                HelperText="Path for video storage" />
                            <MudTextField 
                                Label="Temp Path"
                                @bind-Value="Config.TempPath"
                                HelperText="Path for temporary files" />
                            <MudNumericField 
                                Label="Max Storage (GB)"
                                Value="@(Config.MaxStorageBytes / 1_073_741_824)"
                                ValueChanged="@((long gb) => Config.MaxStorageBytes = gb * 1_073_741_824)"
                                Min="10" Max="10000" />
                        </MudCardContent>
                    </MudCard>
                </MudItem>
                
                <MudItem xs="12" md="6">
                    <MudCard>
                        <MudCardContent>
                            <MudText Typo="Typo.h6">Storage Usage</MudText>
                            <MudProgressLinear 
                                Value="@StoragePercentage" 
                                Color="@(StoragePercentage > 90 ? Color.Error : Color.Primary)" />
                            <MudText>
                                @FormatBytes(StorageUsed) / @FormatBytes(Config.MaxStorageBytes)
                            </MudText>
                        </MudCardContent>
                    </MudCard>
                </MudItem>
            </MudGrid>
        </MudTabPanel>
        
        <MudTabPanel Text="Downloads">
            <MudGrid>
                <MudItem xs="12" md="6">
                    <MudCard>
                        <MudCardContent>
                            <MudText Typo="Typo.h6">Download Settings</MudText>
                            <MudNumericField 
                                Label="Concurrent Downloads"
                                @bind-Value="Config.ConcurrentDownloadLimit"
                                Min="1" Max="10" />
                            <MudNumericField 
                                Label="Retry Attempts"
                                @bind-Value="Config.RetryAttempts"
                                Min="0" Max="10" />
                            <MudSelect 
                                Label="Quality Preference"
                                @bind-Value="Config.QualityPreference">
                                <MudSelectItem Value="@("2160p")">4K (2160p)</MudSelectItem>
                                <MudSelectItem Value="@("1080p")">Full HD (1080p)</MudSelectItem>
                                <MudSelectItem Value="@("720p")">HD (720p)</MudSelectItem>
                                <MudSelectItem Value="@("480p")">SD (480p)</MudSelectItem>
                                <MudSelectItem Value="@("best")">Best Available</MudSelectItem>
                            </MudSelect>
                            <MudNumericField 
                                Label="Rate Limit (Mbps)"
                                @bind-Value="Config.RateLimitMbps"
                                Min="0" Max="1000"
                                HelperText="0 = unlimited" />
                        </MudCardContent>
                    </MudCard>
                </MudItem>
            </MudGrid>
        </MudTabPanel>
        
        <MudTabPanel Text="Security">
            <MudGrid>
                <MudItem xs="12" md="6">
                    <MudCard>
                        <MudCardContent>
                            <MudText Typo="Typo.h6">Password Policy</MudText>
                            <MudNumericField 
                                Label="Minimum Length"
                                @bind-Value="Config.PasswordMinLength"
                                Min="6" Max="32" />
                            <MudSwitch 
                                @bind-Checked="Config.RequireDigit"
                                Label="Require Digit" />
                            <MudSwitch 
                                @bind-Checked="Config.RequireUppercase"
                                Label="Require Uppercase" />
                        </MudCardContent>
                    </MudCard>
                </MudItem>
                
                <MudItem xs="12" md="6">
                    <MudCard>
                        <MudCardContent>
                            <MudText Typo="Typo.h6">Session Settings</MudText>
                            <MudNumericField 
                                Label="JWT Expiry (minutes)"
                                @bind-Value="Config.JwtExpiryMinutes"
                                Min="5" Max="1440" />
                            <MudNumericField 
                                Label="Refresh Token Expiry (days)"
                                @bind-Value="Config.RefreshTokenExpiryDays"
                                Min="1" Max="365" />
                        </MudCardContent>
                    </MudCard>
                </MudItem>
            </MudGrid>
        </MudTabPanel>
    </MudTabs>
    
    <MudPaper Class="pa-4 mt-4">
        <MudButton 
            Color="Color.Primary" 
            Variant="Variant.Filled"
            OnClick="SaveConfiguration">
            Save Changes
        </MudButton>
        <MudButton 
            Color="Color.Default" 
            Variant="Variant.Text"
            OnClick="CancelChanges"
            Class="ml-2">
            Cancel
        </MudButton>
    </MudPaper>
</MudContainer>

@code {
    private SystemConfiguration Config = new();
    private SystemConfiguration OriginalConfig;
    private long StorageUsed;
    private double StoragePercentage => (double)StorageUsed / Config.MaxStorageBytes * 100;
    
    protected override async Task OnInitializedAsync()
    {
        Config = await ConfigService.GetConfigurationAsync();
        OriginalConfig = Config.Clone(); // Deep clone for cancel functionality
        StorageUsed = await StorageService.GetUsedSpaceAsync();
    }
    
    private async Task SaveConfiguration()
    {
        await ConfigService.UpdateConfigurationAsync(Config);
        Snackbar.Add("Configuration saved successfully", Severity.Success);
    }
    
    private void CancelChanges()
    {
        Config = OriginalConfig.Clone();
    }
}
```

## Simplified Deployment

### Docker Container (No Environment Variables)

```dockerfile
FROM mcr.microsoft.com/dotnet/aspnet:8.0-alpine AS runtime
WORKDIR /app

# Install dependencies
RUN apk add --no-cache python3 py3-pip ffmpeg \
    && pip3 install --no-cache-dir --break-system-packages yt-dlp

# Create directories with proper permissions
RUN mkdir -p /data /media /config \
    && chmod 755 /data /media /config

# Copy application
COPY --from=build /app/publish .

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
    CMD wget --spider -q http://localhost:8080/health || exit 1

# Volume mounts
VOLUME ["/data", "/media"]

# No environment variables needed - all config in database
ENTRYPOINT ["dotnet", "VideoJockey.dll"]
```

### Docker Compose (Simplified)

```yaml
version: '3.8'

services:
  videojockey:
    image: videojockey:latest
    container_name: videojockey
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - ./data:/data     # SQLite database and logs
      - ./media:/media   # Video storage
    # No environment variables needed!
```

### First-Run Instructions

```bash
# 1. Start the container
docker-compose up -d

# 2. Open browser to http://localhost:8080
# 3. Complete the setup wizard
# 4. System is ready to use!
```

## Startup Service

```csharp
public class Program
{
    public static async Task Main(string[] args)
    {
        var builder = WebApplication.CreateBuilder(args);
        
        // Configure SQLite
        var dataPath = Path.Combine(
            Environment.GetEnvironmentVariable("DATA_PATH") ?? "/data",
            "videojockey.db");
            
        builder.Services.AddDbContext<VideoJockeyDbContext>(options =>
            options.UseSqlite($"Data Source={dataPath}"));
        
        // Add Data Protection for encryption
        builder.Services.AddDataProtection()
            .PersistKeysToFileSystem(new DirectoryInfo("/data/keys"))
            .SetApplicationName("VideoJockey");
        
        // Add services
        builder.Services.AddScoped<IConfigurationService, ConfigurationService>();
        builder.Services.AddMemoryCache();
        
        // Add Blazor
        builder.Services.AddRazorComponents()
            .AddInteractiveServerComponents();
        
        var app = builder.Build();
        
        // Ensure database exists and is migrated
        using (var scope = app.Services.CreateScope())
        {
            var context = scope.ServiceProvider
                .GetRequiredService<VideoJockeyDbContext>();
            await context.Database.MigrateAsync();
        }
        
        // Check if system needs initialization
        app.Use(async (context, next) =>
        {
            var configService = context.RequestServices
                .GetRequiredService<IConfigurationService>();
                
            if (!await configService.IsSystemInitializedAsync() 
                && !context.Request.Path.StartsWithSegments("/setup"))
            {
                context.Response.Redirect("/setup");
                return;
            }
            
            await next();
        });
        
        app.MapRazorComponents<App>()
            .AddInteractiveServerRenderMode();
            
        app.MapHealthChecks("/health");
        
        await app.RunAsync();
    }
}
```

## Backup and Restore

### Backup Service

```csharp
public class BackupService
{
    private readonly VideoJockeyDbContext _context;
    private readonly IConfigurationService _configService;
    
    public async Task<byte[]> CreateBackupAsync()
    {
        var config = await _configService.GetConfigurationAsync();
        
        using var memoryStream = new MemoryStream();
        using var archive = new ZipArchive(memoryStream, ZipArchiveMode.Create);
        
        // Backup database
        var dbPath = _context.Database.GetDbConnection().ConnectionString
            .Split('=')[1].Split(';')[0];
        var dbEntry = archive.CreateEntry("database.db");
        using (var entryStream = dbEntry.Open())
        using (var fileStream = File.OpenRead(dbPath))
        {
            await fileStream.CopyToAsync(entryStream);
        }
        
        // Backup configuration as JSON (for reference)
        var configEntry = archive.CreateEntry("configuration.json");
        using (var entryStream = configEntry.Open())
        using (var writer = new StreamWriter(entryStream))
        {
            var json = JsonSerializer.Serialize(config, new JsonSerializerOptions 
            { 
                WriteIndented = true 
            });
            await writer.WriteAsync(json);
        }
        
        return memoryStream.ToArray();
    }
    
    public async Task RestoreBackupAsync(Stream backupStream)
    {
        using var archive = new ZipArchive(backupStream, ZipArchiveMode.Read);
        
        // Restore database
        var dbEntry = archive.GetEntry("database.db");
        if (dbEntry != null)
        {
            var dbPath = _context.Database.GetDbConnection().ConnectionString
                .Split('=')[1].Split(';')[0];
            var backupPath = $"{dbPath}.backup";
            
            // Create backup of current database
            File.Copy(dbPath, backupPath, true);
            
            // Restore from archive
            using var entryStream = dbEntry.Open();
            using var fileStream = File.Create(dbPath);
            await entryStream.CopyToAsync(fileStream);
        }
    }
}
```

## Summary

This architecture provides:

1. **True Self-Contained Deployment**: No environment variables needed
2. **Database-Driven Configuration**: All settings stored in SQLite
3. **First-Run Setup Wizard**: Initialize system through web UI
4. **Settings Management UI**: Modify all configuration through the application
5. **Secure Storage**: API keys encrypted in database using Data Protection API
6. **Simple Deployment**: Just mount volumes and access the web UI
7. **Zero External Dependencies**: Everything configured internally

The system is now truly self-hosted and self-contained, requiring only Docker and volume mounts to run.