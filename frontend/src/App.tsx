import React from 'react';
import { Routes, Route } from 'react-router-dom';
import AppLayout from './components/layout/AppLayout';
import Dashboard from './pages/Dashboard';
import Writing from './pages/Writing';
import Practice from './pages/Practice';
import PracticeHistory from './pages/Practice/History';
import GrowthLog from './pages/GrowthLog';
import Search from './pages/Search';
import Settings from './pages/Settings';
import UploadPage from './pages/Upload';
import PortfolioPage from './pages/Portfolio';
import HotTopicsPage from './pages/HotTopics';
import PodcastPage from './pages/Podcast';
// import QuotesAndMaterialsPage from './pages/QuotesAndMaterials'; // 临时注释,完整页面有问题
import QuotesAndMaterialsTest from './pages/QuotesAndMaterials/Test';

const App: React.FC = () => {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/writing" element={<Writing />} />
        <Route path="/practice" element={<Practice />} />
        <Route path="/practice/history" element={<PracticeHistory />} />
        <Route path="/growth-log" element={<GrowthLog />} />
        <Route path="/search" element={<Search />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/portfolio" element={<PortfolioPage />} />
        <Route path="/hot-topics" element={<HotTopicsPage />} />
        <Route path="/podcast" element={<PodcastPage />} />
        <Route path="/quotes-materials" element={<QuotesAndMaterialsTest />} />
        {/* <Route path="/quotes-materials" element={<QuotesAndMaterialsPage />} /> */}
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </AppLayout>
  );
};

export default App;
