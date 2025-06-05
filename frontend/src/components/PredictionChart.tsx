import React from 'react';
import {
  Box,
  Paper,
  Typography,
  CircularProgress,
  useTheme,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Legend,
} from 'recharts';

interface PredictionData {
  predicted_value: number;
  mean_value?: number;
  price_range?: {
    low: number;
    high: number;
  };
  category?: string;
  factors?: {
    base_value: number;
    trim_multiplier: number;
    condition_multiplier: number;
    mileage_multiplier: number;
  };
  confidence?: string;
  year: number;
}

interface PredictionChartProps {
  data: PredictionData | null;
  isLoading: boolean;
}

const LoadingOverlay: React.FC = () => {
  return (
    <Box
      sx={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(255, 255, 255, 0.8)',
        zIndex: 1,
      }}
    >
      <CircularProgress size={60} />
      <Typography variant="h6" sx={{ mt: 2 }}>
        Analyzing Market Data...
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
        Calculating value over time
      </Typography>
    </Box>
  );
};

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

const PredictionChart: React.FC<PredictionChartProps> = ({ data, isLoading }) => {
  const theme = useTheme();

  if (!data) {
    return (
      <Paper elevation={3} sx={{ p: 3, minHeight: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Typography variant="h6" color="text.secondary">
          Enter car details to see value prediction
        </Typography>
      </Paper>
    );
  }

  // Generate 10 years of predictions
  const currentYear = new Date().getFullYear();
  const chartData = Array.from({ length: 10 }, (_, index) => {
    const yearOffset = index;
    const depreciation = Math.pow(0.85, yearOffset); // 15% annual depreciation
    const predictedValue = data.predicted_value * depreciation;
    const meanValue = data.mean_value ? data.mean_value * depreciation : undefined;
    const lowRange = data.price_range ? data.price_range.low * depreciation : undefined;
    const highRange = data.price_range ? data.price_range.high * depreciation : undefined;

    return {
      year: currentYear + yearOffset,
      predictedValue,
      meanValue,
      lowRange,
      highRange,
    };
  });

  const factors = data.factors || {
    base_value: 0,
    trim_multiplier: 1,
    condition_multiplier: 1,
    mileage_multiplier: 1
  };

  return (
    <Paper
      elevation={3}
      sx={{
        p: 3,
        position: 'relative',
        minHeight: '400px',
        transition: 'opacity 0.3s ease',
        opacity: isLoading ? 0.7 : 1,
      }}
    >
      {isLoading && <LoadingOverlay />}

      <Typography variant="h6" gutterBottom>
        Value Prediction Over Time {data.category ? `(${data.category})` : ''}
      </Typography>

      <Box sx={{ mt: 3, height: 300 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="year" 
              tickFormatter={(year) => year.toString()}
            />
            <YAxis
              tickFormatter={formatCurrency}
              domain={[
                (dataMin: number) => Math.floor(dataMin * 0.8),
                (dataMax: number) => Math.ceil(dataMax * 1.2),
              ]}
            />
            <Tooltip
              formatter={(value: number) => formatCurrency(value)}
              labelFormatter={(year) => `Year: ${year}`}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="predictedValue"
              name="Predicted Value"
              stroke={theme.palette.primary.main}
              strokeWidth={2}
              dot={{ r: 4 }}
            />
            {data.mean_value && (
              <Line
                type="monotone"
                dataKey="meanValue"
                name="Market Average"
                stroke={theme.palette.secondary.main}
                strokeWidth={2}
                dot={{ r: 4 }}
              />
            )}
            {data.price_range && (
              <>
                <Line
                  type="monotone"
                  dataKey="lowRange"
                  name="Minimum Range"
                  stroke={theme.palette.error.main}
                  strokeDasharray="5 5"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="highRange"
                  name="Maximum Range"
                  stroke={theme.palette.success.main}
                  strokeDasharray="5 5"
                  dot={false}
                />
              </>
            )}
          </LineChart>
        </ResponsiveContainer>
      </Box>

      <Box sx={{ mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Current Value Breakdown
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Base Value: {formatCurrency(factors.base_value)}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Trim Adjustment: {((factors.trim_multiplier - 1) * 100).toFixed(1)}%
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Condition Impact: {((factors.condition_multiplier - 1) * 100).toFixed(1)}%
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Mileage Impact: {((factors.mileage_multiplier - 1) * 100).toFixed(1)}%
        </Typography>
        {data.price_range && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Current Value Range: {formatCurrency(data.price_range.low)} - {formatCurrency(data.price_range.high)}
          </Typography>
        )}
        {data.confidence && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Confidence Level: {data.confidence.charAt(0).toUpperCase() + data.confidence.slice(1)}
          </Typography>
        )}
      </Box>
    </Paper>
  );
};

export default PredictionChart; 