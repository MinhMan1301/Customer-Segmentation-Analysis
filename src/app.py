from model.attitude_analysis import AttitudeAnalysis

analyzer = AttitudeAnalysis()
result_df = analyzer.run_analysis()
print(result_df)