
import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import TransactionsView from './components/TransactionsView';
import AccountsView from './components/AccountsView';
import InvestmentsView from './components/InvestmentsView';
import CategoriesView from './components/CategoriesView';
import RecurringsView from './components/RecurringsView';
import ReviewPage from './components/ReviewPage';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('Dashboard');
  const [triggerNewCategory, setTriggerNewCategory] = useState(false);
  const [triggerNewAccount, setTriggerNewAccount] = useState(false);

  const handleHeaderButtonClick = () => {
    if (activeTab === 'Categories') {
      setTriggerNewCategory(true);
    } else if (activeTab === 'Accounts') {
      setTriggerNewAccount(true);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[#050910] text-gray-100">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="flex-1 overflow-y-auto pt-4 px-10 pb-16">
        <header className="flex justify-between items-center mb-8 h-16 shrink-0">
          <div className="flex items-center space-x-2">
            <h1 className="text-sm font-semibold text-gray-400">{activeTab}</h1>
          </div>
          <div className="flex items-center space-x-4">
             <button className="p-2 bg-[#0a0f1d] border border-white/5 rounded-lg text-gray-500 hover:text-white transition-colors">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path></svg>
             </button>
             <button
               onClick={handleHeaderButtonClick}
               className="bg-[#3b82f6] hover:bg-[#2563eb] px-5 py-2 rounded-xl text-xs font-bold text-white transition-all shadow-lg shadow-blue-900/10"
             >
               {activeTab === 'Accounts' ? 'Add Account' : activeTab === 'Investments' ? 'Add Asset' : activeTab === 'Categories' ? 'New Category' : activeTab === 'Recurrings' ? 'New Recurring' : 'Add Transaction'}
             </button>
          </div>
        </header>

        <div className="h-[calc(100vh-120px)]">
          {activeTab === 'Dashboard' && <Dashboard setActiveTab={setActiveTab} />}
          {activeTab === 'Transactions' && <TransactionsView />}
          {activeTab === 'Accounts' && (
            <AccountsView
              triggerNewAccount={triggerNewAccount}
              onNewAccountHandled={() => setTriggerNewAccount(false)}
            />
          )}
          {activeTab === 'Investments' && <InvestmentsView />}
          {activeTab === 'Categories' && (
            <CategoriesView
              triggerNewCategory={triggerNewCategory}
              onNewCategoryHandled={() => setTriggerNewCategory(false)}
            />
          )}
          {activeTab === 'Recurrings' && <RecurringsView />}
          {activeTab === 'Review' && <ReviewPage onNavigateToDashboard={() => setActiveTab('Dashboard')} />}
          {activeTab !== 'Dashboard' && activeTab !== 'Transactions' && activeTab !== 'Accounts' && activeTab !== 'Investments' && activeTab !== 'Categories' && activeTab !== 'Recurrings' && activeTab !== 'Review' && (
            <div className="flex flex-col items-center justify-center h-[50vh] text-center">
              <h3 className="text-lg font-bold text-white mb-2">{activeTab} coming soon</h3>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default App;
