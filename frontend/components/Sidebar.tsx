
import React from 'react';
import { MOCK_ACCOUNTS } from '../mockData';
import { AccountType } from '../types';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
  const accountGroups = MOCK_ACCOUNTS.reduce((acc, account) => {
    if (!acc[account.type]) acc[account.type] = [];
    acc[account.type].push(account);
    return acc;
  }, {} as Record<AccountType, typeof MOCK_ACCOUNTS>);

  const navItems = [
    { name: 'Dashboard', icon: (active: boolean) => <svg className={`w-5 h-5 ${active ? 'text-white' : 'text-gray-500'}`} fill="currentColor" viewBox="0 0 20 20"><path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z"></path></svg> },
    { name: 'Transactions', icon: (active: boolean) => <svg className="w-5 h-5 text-gray-500" fill="currentColor" viewBox="0 0 20 20"><path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z"></path></svg> },
    { name: 'Accounts', icon: (active: boolean) => <svg className="w-5 h-5 text-gray-500" fill="currentColor" viewBox="0 0 20 20"><path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4zM18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM5 13a1 1 0 112 0 1 1 0 01-2 0zm7 0a1 1 0 112 0 1 1 0 01-2 0z"></path></svg> },
    { name: 'Investments', icon: (active: boolean) => <svg className="w-5 h-5 text-gray-500" fill="currentColor" viewBox="0 0 20 20"><path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z"></path><path d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z"></path></svg> },
    { name: 'Categories', icon: (active: boolean) => <svg className="w-5 h-5 text-gray-500" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M17.707 9.293a1 1 0 010 1.414l-7 7a1 1 0 01-1.414 0l-7-7A.997.997 0 012 10V5a3 3 0 013-3h5c.256 0 .512.098.707.293l7 7zM5 6a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd"></path></svg> },
    { name: 'Recurrings', icon: (active: boolean) => <svg className="w-5 h-5 text-gray-500" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd"></path></svg> },
  ];

  return (
    <aside className="w-64 flex flex-col bg-[#050910] h-full shrink-0 border-r border-white/5">
      <div className="p-6 h-full flex flex-col">
        <div className="relative mb-8">
          <input 
            type="text" 
            placeholder="Search" 
            className="w-full bg-[#0a0f1d] border border-white/5 rounded-xl py-2 pl-10 pr-4 text-sm font-medium focus:outline-none placeholder-gray-600 text-gray-300"
          />
          <svg className="w-4 h-4 absolute left-3.5 top-2.5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
        </div>

        <nav className="space-y-1 mb-10">
          {navItems.map((item) => (
            <button
              key={item.name}
              onClick={() => setActiveTab(item.name)}
              className={`w-full flex items-center px-3 py-2 text-sm font-semibold rounded-lg transition-all ${
                activeTab === item.name 
                  ? 'bg-[#3b82f6] text-white' 
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <span className="mr-3">{item.icon(activeTab === item.name)}</span>
              {item.name}
            </button>
          ))}
        </nav>

        <div className="flex-1 overflow-y-auto space-y-8 pr-2 custom-scrollbar">
          {(Object.keys(accountGroups) as AccountType[]).map(type => (
            <div key={type}>
              <button className="flex items-center text-[10px] font-black text-gray-600 uppercase tracking-widest mb-4 group w-full">
                <svg className="w-3 h-3 mr-1.5 text-gray-700 rotate-90" fill="currentColor" viewBox="0 0 20 20"><path d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"></path></svg>
                {type === 'Depository' ? 'Cash' : `${type}s`}
              </button>
              <div className="space-y-3.5">
                {accountGroups[type].map(account => (
                  <div key={account.id} className="flex items-center justify-between text-[13px] font-medium leading-none">
                    <div className="flex items-center text-gray-400 min-w-0 pr-4">
                      <div className={`w-1.5 h-1.5 rounded-full ${account.statusColor} mr-2.5 shrink-0`}></div>
                      <span className="truncate">{account.name}</span>
                    </div>
                    <span className="text-gray-400 tabular-nums shrink-0">${account.balance.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-8 space-y-4 pt-6 border-t border-white/5">
          <button className="flex items-center text-xs font-semibold text-gray-500 hover:text-white transition-colors">
            <span className="mr-3">📄</span> Explore
          </button>
          <button className="flex items-center text-xs font-semibold text-gray-500 hover:text-white transition-colors">
            <span className="mr-3">💬</span> Get help
          </button>
          <button className="flex items-center text-xs font-semibold text-gray-500 hover:text-white transition-colors">
            <span className="mr-3">⚙️</span> Settings
          </button>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
