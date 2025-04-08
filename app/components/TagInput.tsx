import { useState, useEffect } from "react"
import CreatableSelect from "react-select/creatable"
import { Label } from "@/components/ui/label"

interface TagInputProps {
  label: string
  description?: string
  value: string[]
  onChange: (values: string[]) => void
  placeholder?: string
  className?: string
}

interface Option {
  label: string
  value: string
}

export function TagInput({
  label,
  description,
  value,
  onChange,
  placeholder = "Type and press enter...",
  className = "",
}: TagInputProps) {
  // Convert string array to options format
  const [options, setOptions] = useState<Option[]>(
    value.map(v => ({ label: v, value: v }))
  )

  // Update options when value prop changes
  useEffect(() => {
    setOptions(value.map(v => ({ label: v, value: v })))
  }, [value])

  const handleChange = (newOptions: readonly Option[] | null) => {
    const newValues = (newOptions || []).map(option => option.value)
    onChange(newValues)
  }

  return (
    <div className={className}>
      <Label>{label}</Label>
      {description && (
        <p className="text-sm text-muted-foreground mb-2">{description}</p>
      )}
      <CreatableSelect
        isMulti
        options={options}
        value={options}
        onChange={handleChange}
        placeholder={placeholder}
        className="react-select-container"
        classNamePrefix="react-select"
        theme={(theme) => ({
          ...theme,
          colors: {
            ...theme.colors,
            primary: 'hsl(var(--primary))',
            primary75: 'hsl(var(--primary) / 0.75)',
            primary50: 'hsl(var(--primary) / 0.5)',
            primary25: 'hsl(var(--primary) / 0.25)',
            danger: 'hsl(var(--destructive))',
            dangerLight: 'hsl(var(--destructive) / 0.1)',
            neutral0: 'hsl(var(--background))',
            neutral5: 'hsl(var(--muted))',
            neutral10: 'hsl(var(--muted))',
            neutral20: 'hsl(var(--border))',
            neutral30: 'hsl(var(--border))',
            neutral40: 'hsl(var(--muted-foreground))',
            neutral50: 'hsl(var(--muted-foreground))',
            neutral60: 'hsl(var(--foreground))',
            neutral70: 'hsl(var(--foreground))',
            neutral80: 'hsl(var(--foreground))',
            neutral90: 'hsl(var(--foreground))',
          },
          borderRadius: 4,
        })}
      />
    </div>
  )
} 