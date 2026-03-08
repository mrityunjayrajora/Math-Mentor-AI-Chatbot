'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import styles from './Sidebar.module.css';

const navItems = [
    { href: '/', label: 'Solve', icon: '🧮', desc: 'Solve problems' },
    { href: '/review', label: 'HITL Review', icon: '👁️', desc: 'Human review' },
    { href: '/memory', label: 'Memory', icon: '🧠', desc: 'Past solutions' },
];

export default function Sidebar() {
    const pathname = usePathname();

    return (
        <aside className={styles.sidebar}>
            <div className={styles.logo}>
                <div className={styles.logoIcon}>∑</div>
                <div>
                    <h1 className={styles.logoTitle}>Math Mentor</h1>
                    <p className={styles.logoSub}>AI Tutor</p>
                </div>
            </div>

            <nav className={styles.nav}>
                {navItems.map((item) => (
                    <Link
                        key={item.href}
                        href={item.href}
                        className={`${styles.navItem} ${pathname === item.href ? styles.active : ''}`}
                    >
                        <span className={styles.navIcon}>{item.icon}</span>
                        <div>
                            <span className={styles.navLabel}>{item.label}</span>
                            <span className={styles.navDesc}>{item.desc}</span>
                        </div>
                    </Link>
                ))}
            </nav>

            <div className={styles.footer}>
                <div className={styles.status}>
                    <span className={styles.statusDot}></span>
                    Backend Connected
                </div>
                <p className={styles.version}>v1.0.0 • RAG + Agents</p>
            </div>
        </aside>
    );
}
