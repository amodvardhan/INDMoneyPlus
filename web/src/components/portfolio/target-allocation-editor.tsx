'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Select, SelectOption } from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import { Badge } from '@/components/ui/badge'
import { AlertCircle, TrendingUp, TrendingDown, Save, RotateCcw, PieChart } from 'lucide-react'
import { formatPercentage } from '@/lib/utils'
import { motion } from 'framer-motion'

export interface AssetClass {
  id: string
  name: string
  description: string
  color: string
}

export interface TargetAllocation {
  [assetClassId: string]: number
}

interface TargetAllocationEditorProps {
  value: TargetAllocation
  onChange: (allocation: TargetAllocation) => void
  assetClasses?: AssetClass[]
}

const DEFAULT_ASSET_CLASSES: AssetClass[] = [
  { id: 'large_cap_equity', name: 'Large Cap Equity', description: 'Large-cap stocks (Nifty 50, S&P 500)', color: '#3B82F6' },
  { id: 'mid_cap_equity', name: 'Mid Cap Equity', description: 'Mid-cap stocks', color: '#8B5CF6' },
  { id: 'small_cap_equity', name: 'Small Cap Equity', description: 'Small-cap stocks', color: '#EC4899' },
  { id: 'international_equity', name: 'International Equity', description: 'US and global stocks', color: '#10B981' },
  { id: 'bonds', name: 'Bonds', description: 'Government and corporate bonds', color: '#F59E0B' },
  { id: 'gold', name: 'Gold', description: 'Gold ETFs and physical gold', color: '#F97316' },
  { id: 'real_estate', name: 'Real Estate', description: 'REITs and real estate funds', color: '#06B6D4' },
  { id: 'cash', name: 'Cash', description: 'Cash and money market funds', color: '#6B7280' },
]

const PRESET_ALLOCATIONS = {
  conservative: {
    large_cap_equity: 30,
    mid_cap_equity: 10,
    small_cap_equity: 5,
    international_equity: 10,
    bonds: 30,
    gold: 10,
    real_estate: 0,
    cash: 5,
  },
  moderate: {
    large_cap_equity: 40,
    mid_cap_equity: 15,
    small_cap_equity: 10,
    international_equity: 15,
    bonds: 15,
    gold: 3,
    real_estate: 0,
    cash: 2,
  },
  aggressive: {
    large_cap_equity: 35,
    mid_cap_equity: 20,
    small_cap_equity: 15,
    international_equity: 20,
    bonds: 5,
    gold: 3,
    real_estate: 2,
    cash: 0,
  },
}

export function TargetAllocationEditor({
  value,
  onChange,
  assetClasses = DEFAULT_ASSET_CLASSES,
}: TargetAllocationEditorProps) {
  const [allocation, setAllocation] = useState<TargetAllocation>(value || {})
  const [selectedPreset, setSelectedPreset] = useState<string>('')

  useEffect(() => {
    if (value) {
      setAllocation(value)
    }
  }, [value])

  const totalAllocation = Object.values(allocation).reduce((sum, val) => sum + (val || 0), 0)
  const isValid = Math.abs(totalAllocation - 100) < 0.01
  const difference = totalAllocation - 100

  const handleChange = (assetClassId: string, newValue: number) => {
    const updated = { ...allocation }
    updated[assetClassId] = Math.max(0, Math.min(100, newValue))
    setAllocation(updated)
    onChange(updated)
    setSelectedPreset('')
  }

  const handlePresetSelect = (preset: string) => {
    if (preset && preset in PRESET_ALLOCATIONS) {
      const presetAlloc = PRESET_ALLOCATIONS[preset as keyof typeof PRESET_ALLOCATIONS]
      setAllocation(presetAlloc)
      onChange(presetAlloc)
      setSelectedPreset(preset)
    }
  }

  const handleReset = () => {
    const reset: TargetAllocation = {}
    assetClasses.forEach((ac) => {
      reset[ac.id] = 0
    })
    setAllocation(reset)
    onChange(reset)
    setSelectedPreset('')
  }

  const presetOptions: SelectOption[] = [
    { value: '', label: 'Custom Allocation' },
    { value: 'conservative', label: 'Conservative (Low Risk)' },
    { value: 'moderate', label: 'Moderate (Balanced)' },
    { value: 'aggressive', label: 'Aggressive (High Risk)' },
  ]

  // Calculate pie chart data
  const pieData = assetClasses
    .filter((ac) => (allocation[ac.id] || 0) > 0)
    .map((ac) => ({
      ...ac,
      value: allocation[ac.id] || 0,
    }))
    .sort((a, b) => b.value - a.value)

  let currentAngle = 0
  const pieSegments = pieData.map((item) => {
    const angle = (item.value / 100) * 360
    const segment = {
      ...item,
      startAngle: currentAngle,
      endAngle: currentAngle + angle,
    }
    currentAngle += angle
    return segment
  })

  return (
    <div className="space-y-6">
      {/* Preset Selector */}
      <div className="flex items-center gap-4">
        <label className="text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">
          Quick Presets:
        </label>
        <Select
          value={selectedPreset}
          onChange={(e) => handlePresetSelect(e.target.value)}
          options={presetOptions}
          className="flex-1"
        />
        <Button
          variant="outline"
          size="sm"
          onClick={handleReset}
          className="whitespace-nowrap"
        >
          <RotateCcw className="h-4 w-4 mr-2" />
          Reset
        </Button>
      </div>

      {/* Visual Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Pie Chart Visualization */}
        <Card className="border-2">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <PieChart className="h-5 w-5" />
              Allocation Visualization
            </CardTitle>
          </CardHeader>
          <CardContent>
            {totalAllocation > 0 ? (
              <div className="flex items-center justify-center">
                <svg width="200" height="200" viewBox="0 0 200 200" className="transform -rotate-90">
                  {pieSegments.map((segment, idx) => {
                    const startAngleRad = (segment.startAngle * Math.PI) / 180
                    const endAngleRad = (segment.endAngle * Math.PI) / 180
                    const largeArcFlag = segment.value > 50 ? 1 : 0

                    const x1 = 100 + 80 * Math.cos(startAngleRad)
                    const y1 = 100 + 80 * Math.sin(startAngleRad)
                    const x2 = 100 + 80 * Math.cos(endAngleRad)
                    const y2 = 100 + 80 * Math.sin(endAngleRad)

                    return (
                      <path
                        key={segment.id}
                        d={`M 100 100 L ${x1} ${y1} A 80 80 0 ${largeArcFlag} 1 ${x2} ${y2} Z`}
                        fill={segment.color}
                        stroke="white"
                        strokeWidth="2"
                        className="hover:opacity-80 transition-opacity"
                      />
                    )
                  })}
                </svg>
              </div>
            ) : (
              <div className="flex items-center justify-center h-[200px] text-gray-400">
                Set allocations to see visualization
              </div>
            )}
          </CardContent>
        </Card>

        {/* Summary Stats */}
        <Card className="border-2">
          <CardHeader>
            <CardTitle className="text-lg">Summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Total Allocation:</span>
              <div className="flex items-center gap-2">
                <span className={`font-bold text-lg ${isValid ? 'text-green-600' : 'text-red-600'}`}>
                  {formatPercentage(totalAllocation)}
                </span>
                {isValid ? (
                  <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                    Valid
                  </Badge>
                ) : (
                  <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">
                    {difference > 0 ? 'Over' : 'Under'} by {formatPercentage(Math.abs(difference))}
                  </Badge>
                )}
              </div>
            </div>
            {!isValid && (
              <div className="flex items-start gap-2 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
                <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
                <p className="text-sm text-yellow-800 dark:text-yellow-200">
                  Total allocation must equal 100%. Adjust the sliders to fix this.
                </p>
              </div>
            )}
            <div className="pt-4 border-t">
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">Top Allocations:</div>
              <div className="space-y-1">
                {pieData.slice(0, 3).map((item) => (
                  <div key={item.id} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: item.color }}
                      />
                      <span>{item.name}</span>
                    </div>
                    <span className="font-medium">{formatPercentage(item.value)}</span>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Allocation Inputs */}
      <Card className="border-2">
        <CardHeader>
          <CardTitle className="text-lg">Set Target Allocations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {assetClasses.map((assetClass) => {
              const currentValue = allocation[assetClass.id] || 0
              return (
                <motion.div
                  key={assetClass.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <div
                          className="w-4 h-4 rounded-full"
                          style={{ backgroundColor: assetClass.color }}
                        />
                        <label className="font-medium text-gray-900 dark:text-gray-100">
                          {assetClass.name}
                        </label>
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {assetClass.description}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <Input
                        type="number"
                        min="0"
                        max="100"
                        step="0.1"
                        value={currentValue.toFixed(1)}
                        onChange={(e) => {
                          const val = parseFloat(e.target.value) || 0
                          handleChange(assetClass.id, val)
                        }}
                        className="w-20 text-right"
                      />
                      <span className="text-sm font-medium text-gray-600 dark:text-gray-400 w-10">
                        %
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <Slider
                      min={0}
                      max={100}
                      step={0.1}
                      value={currentValue}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value) || 0
                        handleChange(assetClass.id, val)
                      }}
                      className="flex-1"
                    />
                    <div className="flex items-center gap-1 text-xs text-gray-500 w-16 justify-end">
                      {currentValue > 0 && (
                        <>
                          {currentValue > (allocation[assetClass.id] || 0) ? (
                            <TrendingUp className="h-3 w-3 text-green-500" />
                          ) : (
                            <TrendingDown className="h-3 w-3 text-red-500" />
                          )}
                        </>
                      )}
                    </div>
                  </div>
                </motion.div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

