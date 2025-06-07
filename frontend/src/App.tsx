import React, { useState } from 'react';
import {
  ThemeProvider,
  CssBaseline,
  Container,
  Box,
  Typography,
  Paper,
} from '@mui/material';
import CarPredictionForm from './components/CarPredictionForm';
import theme from './theme';
import DirectionsCarIcon from '@mui/icons-material/DirectionsCar';

function App() {
  const [predictionData, setPredictionData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handlePrediction = (data: any) => {
    setPredictionData(data);
  };

  const handleLoadingChange = (loading: boolean) => {
    setIsLoading(loading);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box
        sx={{
          minHeight: '100vh',
          background: theme.palette.background.default,
          py: 4,
        }}
      >
        <Container maxWidth="lg">
          <Paper
            elevation={0}
            sx={{
              textAlign: 'center',
              p: 4,
              mb: 4,
              background: theme.palette.background.paper,
              borderRadius: 2,
            }}
          >
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 2,
                mb: 2,
              }}
            >
              <DirectionsCarIcon
                sx={{
                  fontSize: 40,
                  color: theme.palette.primary.main,
                }}
              />
              <Typography
                variant="h1"
                component="h1"
                sx={{
                  color: theme.palette.primary.main,
                  fontWeight: 'bold',
                }}
              >
                CarSeer
              </Typography>
            </Box>
            <Typography
              variant="h5"
              sx={{
                color: theme.palette.text.secondary,
                mb: 4,
                fontWeight: 500,
              }}
            >
              Professional car value predictions
            </Typography>
          </Paper>
          <CarPredictionForm 
            onPrediction={handlePrediction}
            onLoadingChange={handleLoadingChange}
          />
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App;
