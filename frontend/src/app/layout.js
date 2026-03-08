import './globals.css';
import Sidebar from '@/components/layout/Sidebar';

export const metadata = {
  title: 'Math Mentor — AI Math Tutor',
  description: 'Multimodal Math Mentor powered by RAG + Multi-Agent System',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <div className="app-layout">
          <Sidebar />
          <main className="main-content">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
