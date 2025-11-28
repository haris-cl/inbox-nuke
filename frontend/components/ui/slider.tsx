import * as React from "react"
import { cn } from "@/lib/utils"

export interface SliderProps extends React.InputHTMLAttributes<HTMLInputElement> {
  min?: number
  max?: number
  step?: number
  value?: number
  onValueChange?: (value: number) => void
  showValue?: boolean
  showLabels?: boolean
}

const Slider = React.forwardRef<HTMLInputElement, SliderProps>(
  ({
    className,
    min = 0,
    max = 100,
    step = 1,
    value = 50,
    onValueChange,
    showValue = false,
    showLabels = false,
    ...props
  }, ref) => {
    const [internalValue, setInternalValue] = React.useState(value)

    React.useEffect(() => {
      setInternalValue(value)
    }, [value])

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = Number(e.target.value)
      setInternalValue(newValue)
      onValueChange?.(newValue)
    }

    return (
      <div className="space-y-2">
        <div className="relative">
          <input
            type="range"
            ref={ref}
            min={min}
            max={max}
            step={step}
            value={internalValue}
            onChange={handleChange}
            className={cn(
              "w-full h-2 bg-secondary rounded-lg appearance-none cursor-pointer",
              "[&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary",
              "[&::-moz-range-thumb]:w-4 [&::-moz-range-thumb]:h-4 [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:bg-primary [&::-moz-range-thumb]:border-0",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
              "disabled:cursor-not-allowed disabled:opacity-50",
              className
            )}
            {...props}
          />
        </div>
        {(showValue || showLabels) && (
          <div className="flex justify-between text-xs text-muted-foreground">
            {showLabels && <span>{min}</span>}
            {showValue && <span className="font-medium text-foreground">{internalValue}</span>}
            {showLabels && <span>{max}</span>}
          </div>
        )}
      </div>
    )
  }
)
Slider.displayName = "Slider"

export { Slider }
