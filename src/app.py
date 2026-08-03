from model.AttitudeAnalysis import AttitudeAnalysis

if __name__ == "__main__":
    analyzer = AttitudeAnalysis()
    analyzer.print_summary()
    analyzer.generate_charts()