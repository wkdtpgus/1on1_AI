import React from 'react';

interface RadioOption {
  value: string;
  label: string;
}

interface RadioGroupProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'value'> {
  label: string;
  options: RadioOption[];
  name: string;
  value: string;
}

const RadioGroup: React.FC<RadioGroupProps> = ({ label, options, name, value, ...props }) => {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700">{label}</label>
      <div className="mt-2 flex space-x-4">
        {options.map((option) => (
          <div key={option.value} className="flex items-center">
            <input
              id={`${name}-${option.value}`}
              name={name}
              type="radio"
              value={option.value}
              className="h-4 w-4 border-gray-300 text-blue-600 focus:ring-blue-500"
              checked={option.value === value}
              {...props}
            />
            <label htmlFor={`${name}-${option.value}`} className="ml-2 block text-sm text-gray-900">
              {option.label}
            </label>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RadioGroup;
