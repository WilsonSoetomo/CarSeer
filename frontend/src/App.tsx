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
          background: `linear-gradient(135deg, ${theme.palette.background.default} 0%, #FFE5E5 100%)`,
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
              background: 'rgba(255, 255, 255, 0.9)',
              backdropFilter: 'blur(10px)',
              borderRadius: '24px',
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
                  animation: 'float 3s ease-in-out infinite',
                  '@keyframes float': {
                    '0%': {
                      transform: 'translateY(0px)',
                    },
                    '50%': {
                      transform: 'translateY(-10px)',
                    },
                    '100%': {
                      transform: 'translateY(0px)',
                    },
                  },
                }}
              />
              <Typography
                variant="h1"
                component="h1"
                sx={{
                  background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  color: 'transparent',
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
              Predict your car's value with a touch of magic ✨
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
