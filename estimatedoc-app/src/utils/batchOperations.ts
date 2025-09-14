import { CalculatorSettings } from '../types';

export const setAllFieldTimes = (settings: CalculatorSettings, value: number): CalculatorSettings => {
  const updatedFieldTimeEstimates = { ...settings.fieldTimeEstimates };
  
  Object.keys(updatedFieldTimeEstimates).forEach(field => {
    const fieldKey = field as keyof typeof updatedFieldTimeEstimates;
    updatedFieldTimeEstimates[fieldKey] = {
      ...updatedFieldTimeEstimates[fieldKey],
      current: value
    };
  });
  
  return {
    ...settings,
    fieldTimeEstimates: updatedFieldTimeEstimates
  };
};

export const increaseAllFieldTimes = (settings: CalculatorSettings, percentage: number): CalculatorSettings => {
  const updatedFieldTimeEstimates = { ...settings.fieldTimeEstimates };
  
  Object.keys(updatedFieldTimeEstimates).forEach(field => {
    const fieldKey = field as keyof typeof updatedFieldTimeEstimates;
    const currentValue = updatedFieldTimeEstimates[fieldKey].current;
    const newValue = Math.min(
      updatedFieldTimeEstimates[fieldKey].max,
      Math.round(currentValue * (1 + percentage / 100))
    );
    
    updatedFieldTimeEstimates[fieldKey] = {
      ...updatedFieldTimeEstimates[fieldKey],
      current: newValue
    };
  });
  
  return {
    ...settings,
    fieldTimeEstimates: updatedFieldTimeEstimates
  };
};

export const decreaseAllFieldTimes = (settings: CalculatorSettings, percentage: number): CalculatorSettings => {
  const updatedFieldTimeEstimates = { ...settings.fieldTimeEstimates };
  
  Object.keys(updatedFieldTimeEstimates).forEach(field => {
    const fieldKey = field as keyof typeof updatedFieldTimeEstimates;
    const currentValue = updatedFieldTimeEstimates[fieldKey].current;
    const newValue = Math.max(
      updatedFieldTimeEstimates[fieldKey].min,
      Math.round(currentValue * (1 - percentage / 100))
    );
    
    updatedFieldTimeEstimates[fieldKey] = {
      ...updatedFieldTimeEstimates[fieldKey],
      current: newValue
    };
  });
  
  return {
    ...settings,
    fieldTimeEstimates: updatedFieldTimeEstimates
  };
};