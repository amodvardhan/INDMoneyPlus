'use client'

import { useAuth } from '@/hooks/useAuth'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { motion } from 'framer-motion'
import {
    BookOpen,
    TrendingUp,
    PieChart,
    DollarSign,
    Building2,
    Globe,
    BarChart3,
    Target,
    AlertCircle,
    Info,
    Lightbulb,
    GraduationCap,
} from 'lucide-react'

export default function HandbookPage() {
    const router = useRouter()
    const { user, isAuthenticated, isLoading } = useAuth()

    useEffect(() => {
        if (!isLoading && !isAuthenticated) {
            router.push('/login')
        }
    }, [isAuthenticated, isLoading, router])

    if (isLoading || !isAuthenticated) {
        return (
            <div className="container mx-auto px-4 py-8">
                <Skeleton className="h-64 w-full" />
            </div>
        )
    }

    const sections = [
        {
            id: 'getting-started',
            title: 'Getting Started',
            icon: BookOpen,
            color: 'from-blue-500 to-blue-600',
            content: [
                {
                    heading: 'Welcome to Portfolio+',
                    text: 'Portfolio+ is your intelligent portfolio management platform that helps you track, analyze, and optimize your investments across multiple brokers and markets.',
                },
                {
                    heading: 'Key Features',
                    items: [
                        'Multi-broker portfolio aggregation',
                        'AI-powered portfolio analysis',
                        'Automated rebalancing proposals',
                        'Real-time market data',
                        'Tax-efficient investment strategies',
                        'Educational resources and insights',
                    ],
                },
            ],
        },
        {
            id: 'portfolio-basics',
            title: 'Understanding Your Portfolio',
            icon: PieChart,
            color: 'from-purple-500 to-purple-600',
            content: [
                {
                    heading: 'What is a Portfolio?',
                    text: 'A portfolio is a collection of investments (stocks, bonds, ETFs, mutual funds, etc.) that you own. Your portfolio represents your total investment holdings across all your accounts.',
                },
                {
                    heading: 'Portfolio Components',
                    items: [
                        'Stocks: Ownership shares in companies',
                        'Bonds: Fixed-income securities',
                        'ETFs: Exchange-traded funds tracking indices',
                        'Mutual Funds: Professionally managed investment pools',
                        'Cash: Money market funds and cash reserves',
                        'Alternative Investments: Gold, real estate, commodities',
                    ],
                },
                {
                    heading: 'Portfolio Metrics',
                    items: [
                        'Total Valuation: Current market value of all holdings',
                        'Cost Basis: Original purchase price of investments',
                        'P&L (Profit & Loss): Gain or loss on investments',
                        'Allocation: Percentage distribution across asset classes',
                        'Diversification: Spread of risk across different investments',
                    ],
                },
            ],
        },
        {
            id: 'asset-classes',
            title: 'Asset Classes Explained',
            icon: Building2,
            color: 'from-green-500 to-green-600',
            content: [
                {
                    heading: 'Equity (Stocks)',
                    text: 'Stocks represent ownership in companies. They offer potential for growth but come with higher risk.',
                    subItems: [
                        'Large Cap: Established companies with stable earnings (e.g., Reliance, TCS, Apple)',
                        'Mid Cap: Medium-sized companies with growth potential',
                        'Small Cap: Smaller companies with higher growth potential and risk',
                        'International: Stocks from global markets (US, Europe, etc.)',
                    ],
                },
                {
                    heading: 'Fixed Income (Bonds)',
                    text: 'Bonds are loans you make to governments or corporations. They provide regular interest payments and are generally less risky than stocks.',
                },
                {
                    heading: 'Gold',
                    text: 'Gold acts as a hedge against inflation and currency fluctuations. It can be held as physical gold or through Gold ETFs.',
                },
                {
                    heading: 'Real Estate',
                    text: 'Real estate investments can be made through REITs (Real Estate Investment Trusts) or real estate mutual funds.',
                },
                {
                    heading: 'Cash',
                    text: 'Cash and money market funds provide liquidity and safety but offer lower returns.',
                },
            ],
        },
        {
            id: 'rebalancing',
            title: 'Portfolio Rebalancing',
            icon: Target,
            color: 'from-orange-500 to-orange-600',
            content: [
                {
                    heading: 'What is Rebalancing?',
                    text: 'Rebalancing is the process of realigning your portfolio back to your target allocation. Over time, market movements can cause your actual allocation to drift from your desired allocation.',
                },
                {
                    heading: 'Why Rebalance?',
                    items: [
                        'Maintain your desired risk level',
                        'Lock in gains from outperforming assets',
                        'Buy more of underperforming assets at lower prices',
                        'Stay aligned with your investment goals',
                        'Reduce portfolio risk over time',
                    ],
                },
                {
                    heading: 'How to Rebalance',
                    steps: [
                        'Set your target allocation for each asset class',
                        'Review your current holdings and their allocation',
                        'Generate a rebalancing proposal using our AI',
                        'Review the proposed trades and estimated costs',
                        'Approve and execute the rebalancing trades',
                    ],
                },
                {
                    heading: 'Rebalancing Strategies',
                    items: [
                        'Time-based: Rebalance quarterly or annually',
                        'Threshold-based: Rebalance when allocation drifts by 5% or more',
                        'Hybrid: Combine time and threshold approaches',
                    ],
                },
            ],
        },
        {
            id: 'stocks',
            title: 'Understanding Stocks',
            icon: TrendingUp,
            color: 'from-red-500 to-red-600',
            content: [
                {
                    heading: 'What are Stocks?',
                    text: 'Stocks (also called shares or equities) represent ownership in a company. When you buy a stock, you become a partial owner of that company.',
                },
                {
                    heading: 'How Stocks Work',
                    items: [
                        'Companies issue stocks to raise capital',
                        'Stocks are traded on exchanges (NSE, BSE, NYSE, NASDAQ)',
                        'Stock prices fluctuate based on supply and demand',
                        'You can profit through dividends and capital appreciation',
                    ],
                },
                {
                    heading: 'Types of Stocks',
                    items: [
                        'Common Stocks: Voting rights and dividend payments',
                        'Preferred Stocks: Fixed dividends, no voting rights',
                        'Growth Stocks: Companies expected to grow faster',
                        'Value Stocks: Undervalued companies with potential',
                        'Dividend Stocks: Regular dividend payments',
                    ],
                },
                {
                    heading: 'Stock Market Basics',
                    items: [
                        'Market Hours: Trading happens during exchange hours',
                        'Bid/Ask: The price buyers offer vs. sellers ask',
                        'Volume: Number of shares traded',
                        'Market Cap: Total value of company (price × shares)',
                        'P/E Ratio: Price-to-earnings ratio (valuation metric)',
                    ],
                },
            ],
        },
        {
            id: 'ipos',
            title: 'IPOs (Initial Public Offerings)',
            icon: DollarSign,
            color: 'from-indigo-500 to-indigo-600',
            content: [
                {
                    heading: 'What is an IPO?',
                    text: 'An Initial Public Offering (IPO) is when a private company offers its shares to the public for the first time. It allows the company to raise capital from public investors.',
                },
                {
                    heading: 'IPO Process',
                    steps: [
                        'Company files with regulatory body (SEBI in India, SEC in US)',
                        'Investment banks underwrite the offering',
                        'Company sets a price range for shares',
                        'Investors can apply during the IPO period',
                        'Shares are allocated and listed on stock exchange',
                        'Trading begins on the exchange',
                    ],
                },
                {
                    heading: 'Should You Invest in IPOs?',
                    items: [
                        'Pros: Potential for high returns, early access to growth companies',
                        'Cons: Higher risk, limited historical data, potential overvaluation',
                        'Research: Read the prospectus, understand the business model',
                        'Diversification: Don\'t put all your money in IPOs',
                    ],
                },
                {
                    heading: 'IPO Application Process',
                    items: [
                        'Check IPO details (price range, lot size, dates)',
                        'Apply through your broker or bank',
                        'Allocation is usually done via lottery system',
                        'If allocated, shares are credited to your account',
                        'If not allocated, money is refunded',
                    ],
                },
            ],
        },
        {
            id: 'nfos',
            title: 'NFOs (New Fund Offerings)',
            icon: BarChart3,
            color: 'from-teal-500 to-teal-600',
            content: [
                {
                    heading: 'What is an NFO?',
                    text: 'A New Fund Offering (NFO) is when a mutual fund company launches a new mutual fund scheme and invites investors to invest in it.',
                },
                {
                    heading: 'Types of NFOs',
                    items: [
                        'Equity Funds: Invest primarily in stocks',
                        'Debt Funds: Invest in bonds and fixed-income securities',
                        'Hybrid Funds: Mix of equity and debt',
                        'Index Funds: Track specific market indices',
                        'Sectoral Funds: Focus on specific sectors',
                        'ELSS: Tax-saving equity-linked savings schemes',
                    ],
                },
                {
                    heading: 'NFO vs Existing Funds',
                    items: [
                        'NFOs: New fund, no track record, NAV starts at ₹10',
                        'Existing Funds: Historical performance available, established track record',
                        'Consider: Investment strategy, fund manager experience, expense ratio',
                    ],
                },
                {
                    heading: 'Should You Invest in NFOs?',
                    items: [
                        'Research the fund house and fund manager',
                        'Understand the investment strategy and objectives',
                        'Check expense ratios and fees',
                        'Consider your investment goals and risk tolerance',
                        'Diversify across multiple funds',
                    ],
                },
            ],
        },
        {
            id: 'risk-management',
            title: 'Risk Management',
            icon: AlertCircle,
            color: 'from-yellow-500 to-yellow-600',
            content: [
                {
                    heading: 'Understanding Investment Risk',
                    text: 'All investments carry some level of risk. Understanding and managing risk is crucial for long-term investment success.',
                },
                {
                    heading: 'Types of Risk',
                    items: [
                        'Market Risk: Overall market movements affect your investments',
                        'Company Risk: Specific company performance issues',
                        'Sector Risk: Industry-specific challenges',
                        'Liquidity Risk: Difficulty selling investments quickly',
                        'Inflation Risk: Purchasing power erosion over time',
                        'Currency Risk: Exchange rate fluctuations (for international investments)',
                    ],
                },
                {
                    heading: 'Risk Management Strategies',
                    items: [
                        'Diversification: Spread investments across asset classes and sectors',
                        'Asset Allocation: Balance between stocks, bonds, and other assets',
                        'Regular Rebalancing: Maintain target allocation',
                        'Long-term Perspective: Avoid panic selling during market downturns',
                        'Emergency Fund: Keep 3-6 months expenses in liquid assets',
                    ],
                },
            ],
        },
        {
            id: 'tax-considerations',
            title: 'Tax Considerations',
            icon: Info,
            color: 'from-pink-500 to-pink-600',
            content: [
                {
                    heading: 'Capital Gains Tax',
                    text: 'When you sell investments at a profit, you may owe capital gains tax. Understanding tax implications helps optimize returns.',
                },
                {
                    heading: 'Short-term vs Long-term',
                    items: [
                        'Short-term Capital Gains (STCG): Gains on assets held < 1 year (stocks) or < 3 years (debt)',
                        'Long-term Capital Gains (LTCG): Gains on assets held longer than above periods',
                        'Tax Rates: Vary by asset type and holding period',
                    ],
                },
                {
                    heading: 'Tax-Saving Investments',
                    items: [
                        'ELSS: Equity-linked savings schemes with tax deduction under Section 80C',
                        'PPF: Public Provident Fund',
                        'Tax-saving Fixed Deposits',
                        'NPS: National Pension System',
                    ],
                },
                {
                    heading: 'Tax-Loss Harvesting',
                    text: 'Selling losing investments to offset capital gains can help reduce your tax liability. Consult a tax advisor for personalized advice.',
                },
            ],
        },
        {
            id: 'best-practices',
            title: 'Investment Best Practices',
            icon: Lightbulb,
            color: 'from-cyan-500 to-cyan-600',
            content: [
                {
                    heading: 'Start Early',
                    text: 'The power of compounding works best over long periods. Start investing as early as possible, even with small amounts.',
                },
                {
                    heading: 'Invest Regularly',
                    text: 'Systematic Investment Plans (SIPs) help you invest consistently and benefit from rupee cost averaging.',
                },
                {
                    heading: 'Stay Disciplined',
                    items: [
                        'Stick to your investment plan',
                        'Avoid emotional decisions',
                        'Don\'t try to time the market',
                        'Focus on long-term goals',
                    ],
                },
                {
                    heading: 'Keep Learning',
                    text: 'Continuously educate yourself about investing, markets, and financial planning. Use our AI assistant to ask questions anytime.',
                },
                {
                    heading: 'Review Regularly',
                    text: 'Review your portfolio periodically, but avoid over-trading. Rebalance when needed, but maintain a long-term perspective.',
                },
            ],
        },
    ]

    return (
        <div className="container mx-auto px-4 py-8 max-w-6xl">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-8"
            >
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-3 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl shadow-lg">
                        <GraduationCap className="h-8 w-8 text-white" />
                    </div>
                    <div>
                        <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
                            Investment Handbook
                        </h1>
                        <p className="text-lg text-gray-600 dark:text-gray-400 mt-1">
                            Your comprehensive guide to portfolio management and investing
                        </p>
                    </div>
                </div>
            </motion.div>

            <div className="space-y-6">
                {sections.map((section, idx) => {
                    const Icon = section.icon
                    return (
                        <motion.div
                            key={section.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: idx * 0.1 }}
                        >
                            <Card className="border-2 shadow-lg hover:shadow-xl transition-shadow">
                                <CardHeader className="bg-gradient-to-r from-white to-gray-50 dark:from-gray-900 dark:to-gray-800 border-b">
                                    <div className="flex items-center gap-3">
                                        <div className={`p-2 bg-gradient-to-br ${section.color} rounded-lg shadow-md`}>
                                            <Icon className="h-6 w-6 text-white" />
                                        </div>
                                        <CardTitle className="text-2xl">{section.title}</CardTitle>
                                    </div>
                                </CardHeader>
                                <CardContent className="pt-6">
                                    <div className="space-y-6">
                                        {section.content.map((item, itemIdx) => (
                                            <div key={itemIdx} className="space-y-3">
                                                <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                                                    {item.heading}
                                                </h3>
                                                {item.text && (
                                                    <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                                                        {item.text}
                                                    </p>
                                                )}
                                                {'items' in item && item.items && (
                                                    <ul className="list-disc list-inside space-y-2 text-gray-700 dark:text-gray-300 ml-4">
                                                        {item.items.map((listItem: string, listIdx: number) => (
                                                            <li key={listIdx} className="leading-relaxed">
                                                                {listItem}
                                                            </li>
                                                        ))}
                                                    </ul>
                                                )}
                                                {'steps' in item && item.steps && (
                                                    <ol className="list-decimal list-inside space-y-2 text-gray-700 dark:text-gray-300 ml-4">
                                                        {item.steps.map((step: string, stepIdx: number) => (
                                                            <li key={stepIdx} className="leading-relaxed">
                                                                {step}
                                                            </li>
                                                        ))}
                                                    </ol>
                                                )}
                                                {'subItems' in item && item.subItems && (
                                                    <ul className="list-disc list-inside space-y-2 text-gray-700 dark:text-gray-300 ml-8">
                                                        {item.subItems.map((subItem: string, subIdx: number) => (
                                                            <li key={subIdx} className="leading-relaxed">
                                                                {subItem}
                                                            </li>
                                                        ))}
                                                    </ul>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>
                        </motion.div>
                    )
                })}
            </div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: sections.length * 0.1 }}
                className="mt-8"
            >
                <Card className="border-2 border-primary-200 bg-gradient-to-br from-primary-50 to-primary-100/50 dark:from-primary-950/50 dark:to-primary-900/30">
                    <CardContent className="pt-6">
                        <div className="flex items-start gap-4">
                            <Info className="h-6 w-6 text-primary-600 mt-1 flex-shrink-0" />
                            <div>
                                <h3 className="font-semibold text-lg mb-2 text-gray-900 dark:text-gray-100">
                                    Need More Help?
                                </h3>
                                <p className="text-gray-700 dark:text-gray-300 mb-4">
                                    Our AI assistant is available 24/7 to answer any questions about investing, your portfolio, or market concepts. Just click the chat icon in the bottom right corner!
                                </p>
                                <p className="text-sm text-gray-600 dark:text-gray-400">
                                    <strong>Disclaimer:</strong> This handbook is for educational purposes only. It does not constitute financial advice. Please consult with a qualified financial advisor before making investment decisions.
                                </p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </motion.div>
        </div>
    )
}

