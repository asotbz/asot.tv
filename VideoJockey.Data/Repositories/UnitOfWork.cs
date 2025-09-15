using System;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore.Storage;
using VideoJockey.Core.Entities;
using VideoJockey.Core.Interfaces;
using VideoJockey.Data.Context;

namespace VideoJockey.Data.Repositories
{
    public class UnitOfWork : IUnitOfWork
    {
        private readonly ApplicationDbContext _context;
        private IDbContextTransaction? _transaction;
        private bool _disposed;

        // Repository instances
        private IRepository<Video>? _videos;
        private IRepository<Genre>? _genres;
        private IRepository<Tag>? _tags;
        private IRepository<FeaturedArtist>? _featuredArtists;
        private IRepository<Configuration>? _configurations;
        private IRepository<DownloadQueue>? _downloadQueues;

        public UnitOfWork(ApplicationDbContext context)
        {
            _context = context;
        }

        public IRepository<Video> Videos => _videos ??= new Repository<Video>(_context);
        public IRepository<Genre> Genres => _genres ??= new Repository<Genre>(_context);
        public IRepository<Tag> Tags => _tags ??= new Repository<Tag>(_context);
        public IRepository<FeaturedArtist> FeaturedArtists => _featuredArtists ??= new Repository<FeaturedArtist>(_context);
        public IRepository<Configuration> Configurations => _configurations ??= new Repository<Configuration>(_context);
        public IRepository<DownloadQueue> DownloadQueues => _downloadQueues ??= new Repository<DownloadQueue>(_context);

        public async Task<int> SaveChangesAsync()
        {
            return await _context.SaveChangesAsync();
        }

        public async Task BeginTransactionAsync()
        {
            if (_transaction != null)
            {
                throw new InvalidOperationException("A transaction is already in progress.");
            }

            _transaction = await _context.Database.BeginTransactionAsync();
        }

        public async Task CommitTransactionAsync()
        {
            if (_transaction == null)
            {
                throw new InvalidOperationException("No transaction in progress.");
            }

            try
            {
                await _context.SaveChangesAsync();
                await _transaction.CommitAsync();
            }
            catch
            {
                await RollbackTransactionAsync();
                throw;
            }
            finally
            {
                await _transaction.DisposeAsync();
                _transaction = null;
            }
        }

        public async Task RollbackTransactionAsync()
        {
            if (_transaction == null)
            {
                throw new InvalidOperationException("No transaction in progress.");
            }

            await _transaction.RollbackAsync();
            await _transaction.DisposeAsync();
            _transaction = null;
        }

        protected virtual void Dispose(bool disposing)
        {
            if (!_disposed)
            {
                if (disposing)
                {
                    _transaction?.Dispose();
                    _context.Dispose();
                }
                _disposed = true;
            }
        }

        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }
    }
}