export default function Home() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="col-span-1">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
            <h2 className="text-lg font-semibold mb-4">System Status</h2>
            <div className="space-y-4">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Status</p>
                <p className="text-red-500 font-medium">STOPPED</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Check Interval</p>
                <p className="font-medium">5 minutes</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 