import React, { useState } from 'react';
import { ThemeProvider, createTheme, CssBaseline, Container, Box, Typography } from '@mui/material';
import CarPredictionForm from './components/CarPredictionForm';
import PredictionChart from './components/PredictionChart';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  const [predictionData, setPredictionData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handlePrediction = (data: any) => {
    setPredictionData(data);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="lg">
        <Box sx={{ my: 4 }}>
          <Typography variant="h3" component="h1" gutterBottom align="center">
            CarSeer
          </Typography>
          <Typography variant="h5" component="h2" gutterBottom align="center" color="text.secondary">
            Intelligent Car Value Predictions
          </Typography>
          
          <Box sx={{ mt: 4 }}>
            <CarPredictionForm 
              onPrediction={handlePrediction}
              onLoadingChange={setIsLoading}
            />
          </Box>

          {(predictionData || isLoading) && (
            <Box sx={{ mt: 4 }}>
              <PredictionChart 
                data={predictionData}
                isLoading={isLoading}
              />
            </Box>
          )}
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;
