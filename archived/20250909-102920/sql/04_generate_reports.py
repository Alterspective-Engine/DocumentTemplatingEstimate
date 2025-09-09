#!/usr/bin/env python3
"""
Generate comprehensive reports from EstimateDoc database
Including statistical analysis and estimations for unmatched documents
"""

import psycopg2
import pandas as pd
from datetime import datetime
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'estimatedoc',
    'user': 'estimatedoc_user',
    'password': 'estimatedoc_user'
}

class EstimateDocReporter:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()
        
    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()
            
    def refresh_metrics(self):
        """Refresh all reporting metrics"""
        logger.info("Refreshing all reporting metrics...")
        try:
            self.cursor.execute("SELECT refresh_all_reporting_metrics()")
            self.conn.commit()
            logger.info("Metrics refreshed successfully")
        except Exception as e:
            logger.error(f"Error refreshing metrics: {e}")
            self.conn.rollback()
            
    def generate_comprehensive_report(self):
        """Generate the main comprehensive report"""
        logger.info("Generating comprehensive Excel row report...")
        
        query = """
        SELECT 
            row_id,
            template_code,
            description,
            stated_complexity,
            match_status,
            match_method,
            match_confidence,
            document_id,
            filename,
            total_fields,
            unique_to_doc_fields,
            reusable_fields,
            reusability_ratio,
            if_statements,
            has_scripts,
            script_count,
            total_complexity_score,
            complexity_rating,
            estimation_sample_size,
            fields_stddev,
            complexity_stddev,
            complexity_ci_95,
            data_confidence
        FROM v_final_excel_comprehensive_report
        ORDER BY row_id
        """
        
        df = pd.read_sql_query(query, self.conn)
        
        # Add summary statistics
        matched_count = len(df[df['match_status'] == 'Matched'])
        estimated_count = len(df[df['match_status'] == 'Estimated'])
        total_count = len(df)
        
        logger.info(f"Report generated: {matched_count} matched, {estimated_count} estimated, {total_count} total")
        
        return df
        
    def generate_statistical_summary(self):
        """Generate statistical summary by complexity level"""
        logger.info("Generating statistical summary...")
        
        query = """
        SELECT 
            stated_complexity,
            sample_size,
            avg_total_fields,
            stddev_total_fields,
            ci_95_total_fields,
            avg_unique_fields,
            avg_reusable_fields,
            avg_reusability_pct,
            avg_if_statements,
            avg_script_count,
            avg_complexity_score,
            stddev_complexity_score,
            ci_95_complexity_score,
            cv_complexity_pct
        FROM v_complexity_statistical_summary
        ORDER BY 
            CASE stated_complexity
                WHEN 'Simple' THEN 1
                WHEN 'Moderate' THEN 2
                WHEN 'Medium' THEN 3
                WHEN 'Complex' THEN 4
                ELSE 5
            END
        """
        
        df = pd.read_sql_query(query, self.conn)
        return df
        
    def generate_estimation_quality_report(self):
        """Generate report on estimation quality and confidence"""
        logger.info("Generating estimation quality report...")
        
        query = """
        SELECT 
            stated_complexity,
            matched_count,
            unmatched_count,
            total_count,
            match_rate_pct,
            statistical_sample_size,
            estimation_confidence,
            variability_pct,
            consistency_rating
        FROM v_estimation_quality
        """
        
        df = pd.read_sql_query(query, self.conn)
        return df
        
    def generate_field_reusability_report(self):
        """Generate field reusability analysis"""
        logger.info("Generating field reusability report...")
        
        query = """
        SELECT 
            COUNT(*) as total_fields,
            SUM(CASE WHEN is_reusable THEN 1 ELSE 0 END) as reusable_fields,
            SUM(CASE WHEN is_unique THEN 1 ELSE 0 END) as unique_fields,
            ROUND(100.0 * SUM(CASE WHEN is_reusable THEN 1 ELSE 0 END) / COUNT(*), 2) as reusability_pct,
            AVG(usage_count) as avg_usage_count,
            MAX(usage_count) as max_usage_count,
            AVG(document_count) as avg_document_count,
            MAX(document_count) as max_document_count
        FROM field_reusability_analysis
        """
        
        df = pd.read_sql_query(query, self.conn)
        return df
        
    def save_reports_to_excel(self, output_path='EstimateDoc_Comprehensive_Report.xlsx'):
        """Save all reports to Excel with multiple sheets"""
        logger.info(f"Saving reports to {output_path}...")
        
        # Refresh metrics first
        self.refresh_metrics()
        
        # Generate all reports
        comprehensive = self.generate_comprehensive_report()
        statistical = self.generate_statistical_summary()
        quality = self.generate_estimation_quality_report()
        reusability = self.generate_field_reusability_report()
        
        # Create Excel writer
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Main comprehensive report
            comprehensive.to_excel(writer, sheet_name='Comprehensive Report', index=False)
            
            # Statistical summary
            statistical.to_excel(writer, sheet_name='Statistical Summary', index=False)
            
            # Estimation quality
            quality.to_excel(writer, sheet_name='Estimation Quality', index=False)
            
            # Field reusability
            reusability.to_excel(writer, sheet_name='Field Reusability', index=False)
            
            # Add summary statistics sheet
            summary_stats = self._create_summary_statistics(comprehensive)
            summary_stats.to_excel(writer, sheet_name='Summary', index=False)
            
        logger.info(f"Reports saved successfully to {output_path}")
        
    def _create_summary_statistics(self, df):
        """Create summary statistics DataFrame"""
        summary = {
            'Metric': [],
            'Value': []
        }
        
        # Overall statistics
        summary['Metric'].extend([
            'Total Excel Rows',
            'Matched Documents',
            'Estimated Documents',
            'Match Rate (%)',
            '',
            'Average Total Fields (Matched)',
            'Average Complexity Score (Matched)',
            'Average Reusability Ratio (Matched)',
            '',
            'Documents with Scripts',
            'Documents with IF Statements',
            '',
            'High Confidence Estimates',
            'Medium Confidence Estimates',
            'Low Confidence Estimates',
            'Very Low Confidence Estimates'
        ])
        
        matched_df = df[df['match_status'] == 'Matched']
        estimated_df = df[df['match_status'] == 'Estimated']
        
        summary['Value'].extend([
            len(df),
            len(matched_df),
            len(estimated_df),
            round(100.0 * len(matched_df) / len(df), 1) if len(df) > 0 else 0,
            '',
            round(matched_df['total_fields'].mean(), 1) if len(matched_df) > 0 else 0,
            round(matched_df['total_complexity_score'].mean(), 1) if len(matched_df) > 0 else 0,
            round(matched_df['reusability_ratio'].mean(), 1) if len(matched_df) > 0 else 0,
            '',
            matched_df['has_scripts'].sum() if len(matched_df) > 0 else 0,
            (matched_df['if_statements'] > 0).sum() if len(matched_df) > 0 else 0,
            '',
            (estimated_df['data_confidence'] == 'High').sum() if len(estimated_df) > 0 else 0,
            (estimated_df['data_confidence'] == 'Medium').sum() if len(estimated_df) > 0 else 0,
            (estimated_df['data_confidence'] == 'Low').sum() if len(estimated_df) > 0 else 0,
            (estimated_df['data_confidence'] == 'Very Low').sum() if len(estimated_df) > 0 else 0
        ])
        
        return pd.DataFrame(summary)
        
    def print_analysis_summary(self):
        """Print analysis summary to console"""
        logger.info("\n" + "="*80)
        logger.info("ESTIMATEDOC COMPREHENSIVE ANALYSIS SUMMARY")
        logger.info("="*80)
        
        # Get statistical summary
        stats_df = self.generate_statistical_summary()
        quality_df = self.generate_estimation_quality_report()
        
        logger.info("\n📊 COMPLEXITY LEVEL STATISTICS")
        logger.info("-"*50)
        for _, row in stats_df.iterrows():
            logger.info(f"\n{row['stated_complexity']} (n={row['sample_size']})")
            logger.info(f"  Average Fields: {row['avg_total_fields']:.1f} ± {row['stddev_total_fields']:.1f}")
            logger.info(f"  Complexity Score: {row['avg_complexity_score']:.1f} ± {row['stddev_complexity_score']:.1f}")
            logger.info(f"  95% CI: {row['ci_95_complexity_score']}")
            logger.info(f"  Reusability: {row['avg_reusability_pct']:.1f}%")
            logger.info(f"  IF Statements: {row['avg_if_statements']:.1f}")
            logger.info(f"  Scripts: {row['avg_script_count']:.1f}")
            
        logger.info("\n📈 ESTIMATION QUALITY METRICS")
        logger.info("-"*50)
        for _, row in quality_df.iterrows():
            logger.info(f"\n{row['stated_complexity']}")
            logger.info(f"  Matched: {row['matched_count']}/{row['total_count']} ({row['match_rate_pct']:.1f}%)")
            logger.info(f"  Estimation Confidence: {row['estimation_confidence']}")
            logger.info(f"  Consistency: {row['consistency_rating']} (CV={row['variability_pct']:.1f}%)")


if __name__ == "__main__":
    reporter = EstimateDocReporter()
    
    # Generate and save all reports
    reporter.save_reports_to_excel()
    
    # Print summary to console
    reporter.print_analysis_summary()