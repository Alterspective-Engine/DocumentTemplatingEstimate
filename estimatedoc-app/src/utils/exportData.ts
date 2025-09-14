import { Document } from '../types';

export const exportToCSV = (documents: Document[]): string => {
  const headers = [
    'ID', 'Name', 'Category', 'Complexity', 'Fields', 
    'Estimated Hours', 'Reuse Rate', 'Automation Potential'
  ];
  
  const rows = documents.map(doc => [
    doc.id,
    doc.name,
    doc.category || '',
    doc.complexity || '',
    doc.fields || 0,
    doc.estimatedHours || 0,
    doc.reuseRate || 0,
    doc.automationPotential || 0
  ]);
  
  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
  ].join('\n');
  
  return csvContent;
};

export const downloadCSV = (content: string, filename: string = 'estimatedoc-export.csv') => {
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

export const exportToJSON = (data: any): string => {
  return JSON.stringify(data, null, 2);
};

export const downloadJSON = (data: any, filename: string = 'estimatedoc-export.json') => {
  const content = exportToJSON(data);
  const blob = new Blob([content], { type: 'application/json' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};