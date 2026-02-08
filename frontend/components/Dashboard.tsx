
import React from 'react';
import MonthlySpending from './MonthlySpending';
import NetWorth from './NetWorth';
import TransactionReview from './TransactionReview';
import TopCategories from './TopCategories';
import UpcomingRecurrings from './UpcomingRecurrings';

interface DashboardProps {
  setActiveTab?: (tab: string) => void;
}

const Dashboard: React.FC<DashboardProps> = ({ setActiveTab }) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pb-8">
      {/* Monthly Spending Card */}
      <MonthlySpending />

      {/* Net Worth Card */}
      <NetWorth />

      {/* Transactions to Review */}
      <TransactionReview onNavigateToReview={() => setActiveTab?.('Review')} />

      {/* Top Categories / Budgets */}
      <div className="space-y-6">
        <TopCategories />
        <UpcomingRecurrings />
      </div>
    </div>
  );
};

export default Dashboard;
