# Video Jockey - Music Video Management System

A professional web-based music video library management system inspired by DJ software, designed for collectors, VJs, DJs, and music video enthusiasts.

## 🎬 Features

### Core Functionality
- **Library Management**: Organize and catalog your music video collection
- **Smart Search**: Advanced filtering by artist, genre, year, and more
- **Download Queue**: Managed download system with progress tracking
- **Metadata Enrichment**: Automatic metadata fetching from IMVDb and YouTube
- **Source Verification**: Track official vs. unofficial releases
- **Library Import**: Scan and import existing video collections

### Coming Soon (Roadmap)
- Playlist creation and management
- Social sharing features
- Analytics and insights
- Mobile applications
- Cloud synchronization

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/yourusername/video-jockey.git
cd video-jockey
```

2. Create environment file:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Start the application:
```bash
docker-compose up -d
```

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Local Development

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 📁 Project Structure

```
video-jockey/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Core configuration
│   │   ├── models/      # Database models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── services/    # Business logic
│   │   └── utils/       # Utility functions
│   ├── tests/           # Backend tests
│   └── migrations/      # Database migrations
├── frontend/            # Next.js frontend
│   ├── app/            # Next.js app directory
│   ├── components/     # React components
│   ├── lib/           # Utility libraries
│   └── public/        # Static assets
├── docs/              # Documentation
├── scripts/           # Utility scripts
└── docker-compose.yml # Docker configuration
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Backend
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./data/video_jockey.db
REDIS_URL=redis://redis:6379/0

# External APIs
IMVDB_API_KEY=your-imvdb-api-key
YOUTUBE_API_KEY=your-youtube-api-key

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## 🧪 Testing

### Run Backend Tests
```bash
cd backend
pytest tests/ --cov=app
```

### Run Frontend Tests
```bash
cd frontend
npm test
```

### Run All Tests
```bash
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 📊 API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 Development Roadmap

### Sprint 1: Foundation (Current)
- [x] Project setup and structure
- [x] Basic FastAPI backend
- [x] Next.js frontend setup
- [x] Docker configuration
- [x] CI/CD pipeline

### Sprint 2: Authentication & User Management
- [ ] User registration and login
- [ ] JWT authentication
- [ ] User profiles
- [ ] Password reset

### Sprint 3: Core Video Management
- [ ] Video CRUD operations
- [ ] File upload handling
- [ ] Thumbnail generation
- [ ] Basic search functionality

### Sprint 4: Download Queue
- [ ] Queue management system
- [ ] yt-dlp integration
- [ ] Progress tracking
- [ ] Error handling

See [VideoJockey.roadmap.md](../VideoJockey.roadmap.md) for the complete roadmap.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by the mvOrganizer CLI tool
- Built with FastAPI and Next.js
- Uses IMVDb and YouTube APIs for metadata
- Community contributions and feedback

## 📞 Support

For support, please:
- Check the [Documentation](docs/)
- Open an [Issue](https://github.com/yourusername/video-jockey/issues)
- Join our [Discord Community](https://discord.gg/videojockey)

---

**Video Jockey** - Professional Music Video Management
Made with ❤️ by the Video Jockey Team