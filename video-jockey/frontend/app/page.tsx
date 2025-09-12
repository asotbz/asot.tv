export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm">
        <h1 className="text-4xl font-bold text-center mb-8">
          Video Jockey
        </h1>
        <p className="text-center text-lg text-gray-600 dark:text-gray-400">
          Professional Music Video Management System
        </p>
        <div className="mt-8 flex gap-4 justify-center">
          <button className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
            Get Started
          </button>
          <button className="px-6 py-3 border border-gray-300 dark:border-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
            Learn More
          </button>
        </div>
      </div>
    </main>
  )
}