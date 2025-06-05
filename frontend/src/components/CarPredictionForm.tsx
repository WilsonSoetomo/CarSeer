import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  Paper,
  Typography,
  MenuItem,
  CircularProgress,
} from '@mui/material';
import axios from 'axios';

interface CarPredictionFormProps {
  onPrediction: (data: any) => void;
  onLoadingChange: (isLoading: boolean) => void;
}

interface CarMake {
  id: number;
  name: string;
}

interface CarModel {
  id: number;
  name: string;
  make_id: number;
}

interface CarYear {
  year: number;
}

// Top 75 most common car brands in alphabetical order
const commonCarMakes: CarMake[] = [
  { id: 23, name: 'Acura' },
  { id: 31, name: 'Alfa Romeo' },
  { id: 40, name: 'Aston Martin' },
  { id: 11, name: 'Audi' },
  { id: 35, name: 'Bentley' },
  { id: 9, name: 'BMW' },
  { id: 42, name: 'Bugatti' },
  { id: 19, name: 'Buick' },
  { id: 20, name: 'Cadillac' },
  { id: 74, name: 'Chery' },
  { id: 4, name: 'Chevrolet' },
  { id: 21, name: 'Chrysler' },
  { id: 60, name: 'Citroën' },
  { id: 56, name: 'Daewoo' },
  { id: 67, name: 'Dacia' },
  { id: 16, name: 'Dodge' },
  { id: 30, name: 'Fiat' },
  { id: 38, name: 'Ferrari' },
  { id: 3, name: 'Ford' },
  { id: 73, name: 'Great Wall' },
  { id: 32, name: 'Genesis' },
  { id: 18, name: 'GMC' },
  { id: 72, name: 'Geely' },
  { id: 52, name: 'Hummer' },
  { id: 2, name: 'Honda' },
  { id: 6, name: 'Hyundai' },
  { id: 75, name: 'JAC' },
  { id: 34, name: 'Jaguar' },
  { id: 24, name: 'Infiniti' },
  { id: 55, name: 'Isuzu' },
  { id: 7, name: 'Kia' },
  { id: 68, name: 'Lada' },
  { id: 59, name: 'Lancia' },
  { id: 33, name: 'Land Rover' },
  { id: 12, name: 'Lexus' },
  { id: 22, name: 'Lincoln' },
  { id: 43, name: 'Lucid' },
  { id: 70, name: 'Mahindra' },
  { id: 39, name: 'Maserati' },
  { id: 14, name: 'Mazda' },
  { id: 58, name: 'Maybach' },
  { id: 41, name: 'McLaren' },
  { id: 11, name: 'Mercedes-Benz' },
  { id: 51, name: 'Mercury' },
  { id: 28, name: 'Mitsubishi' },
  { id: 5, name: 'Nissan' },
  { id: 49, name: 'Oldsmobile' },
  { id: 65, name: 'Opel' },
  { id: 61, name: 'Peugeot' },
  { id: 50, name: 'Plymouth' },
  { id: 48, name: 'Pontiac' },
  { id: 45, name: 'Polestar' },
  { id: 26, name: 'Porsche' },
  { id: 17, name: 'Ram' },
  { id: 62, name: 'Renault' },
  { id: 44, name: 'Rivian' },
  { id: 36, name: 'Rolls-Royce' },
  { id: 53, name: 'Saab' },
  { id: 46, name: 'Saturn' },
  { id: 63, name: 'Seat' },
  { id: 64, name: 'Skoda' },
  { id: 57, name: 'Smart' },
  { id: 13, name: 'Subaru' },
  { id: 54, name: 'Suzuki' },
  { id: 69, name: 'Tata' },
  { id: 27, name: 'Tesla' },
  { id: 1, name: 'Toyota' },
  { id: 66, name: 'Vauxhall' },
  { id: 8, name: 'Volkswagen' },
  { id: 25, name: 'Volvo' },
];

const conditions = ['Excellent', 'Good', 'Fair', 'Poor'];

const CarPredictionForm: React.FC<CarPredictionFormProps> = ({ onPrediction, onLoadingChange }) => {
  const [formData, setFormData] = useState({
    make: '',
    model: '',
    trim: '',
    year: new Date().getFullYear(),
    mileage: '',
    condition: 'Good',
    zip_code: ''
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [models, setModels] = useState<CarModel[]>([]);
  const [trims, setTrims] = useState<string[]>([]);
  const [years, setYears] = useState<CarYear[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [loadingTrims, setLoadingTrims] = useState(false);

  // Notify parent of loading state changes
  useEffect(() => {
    onLoadingChange(loading);
  }, [loading, onLoadingChange]);

  // Debug logging for state changes
  useEffect(() => {
    console.log('Form data changed:', formData);
  }, [formData]);

  // Fetch models when make changes
  useEffect(() => {
    const fetchModels = async () => {
      if (!formData.make) {
        setModels([]);
        return;
      }

      setLoadingModels(true);
      try {
        console.log(`Fetching models for ${formData.make}`);
        const response = await axios.get(
          `https://vpic.nhtsa.dot.gov/api/vehicles/getmodelsformake/${encodeURIComponent(formData.make)}?format=json`
        );
        
        const modelsData = response.data.Results
          .map((model: any) => {
            let name = model.Model_Name.trim();
            // Remove make name from the start if it exists
            if (name.toLowerCase().startsWith(formData.make.toLowerCase())) {
              name = name.substring(formData.make.length).trim();
            }
            return {
              id: model.Model_ID,
              name: name,
              make_id: model.Make_ID,
            };
          })
          .filter((model: CarModel) => model.name) // Remove empty names
          .sort((a: CarModel, b: CarModel) => a.name.localeCompare(b.name));

        console.log('Models data:', modelsData);
        setModels(modelsData);
      } catch (err) {
        console.error('Error fetching models:', err);
        setError('Failed to load car models. Please try again.');
        setModels([]);
      } finally {
        setLoadingModels(false);
      }
    };

    fetchModels();
  }, [formData.make]);

  // Fetch trims when model changes
  useEffect(() => {
    const fetchTrims = async () => {
      if (!formData.make || !formData.model) {
        console.log('No make or model selected, clearing trims');
        setTrims([]);
        return;
      }

      setLoadingTrims(true);
      try {
        console.log(`Fetching trims for ${formData.make} ${formData.model}`);
        const response = await axios.get(
          `http://localhost:8000/api/trims/${encodeURIComponent(formData.make)}/${encodeURIComponent(formData.model)}`
        );
        console.log('Trims response:', response.data);
        
        if (response.data.trims && Array.isArray(response.data.trims)) {
          setTrims(response.data.trims);
          console.log('Set trims to:', response.data.trims);
        } else {
          console.warn('Invalid trims data:', response.data);
          setTrims([]);
        }
      } catch (err) {
        console.error('Error fetching trims:', err);
        setError('Failed to load trim options. Please try again.');
        setTrims([]);
      } finally {
        setLoadingTrims(false);
      }
    };

    fetchTrims();
  }, [formData.make, formData.model]);

  // Generate years when model is selected
  useEffect(() => {
    if (formData.model) {
      const currentYear = new Date().getFullYear();
      const yearsData = Array.from({ length: 30 }, (_, i) => ({
        year: currentYear - i,
      })).sort((a, b) => b.year - a.year);
      setYears(yearsData);
    } else {
      setYears([]);
    }
  }, [formData.model]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    console.log(`Handling change for ${name}: ${value}`);
    
    setFormData(prev => {
      const newData = {
        ...prev,
        [name]: value,
      };
      
      // Reset dependent fields when parent field changes
      if (name === 'make') {
        newData.model = '';
        newData.trim = '';
        newData.year = new Date().getFullYear();
      } else if (name === 'model') {
        newData.trim = '';
        newData.year = new Date().getFullYear();
      }
      
      return newData;
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      console.log('Submitting form data:', formData);
      const response = await axios.post('http://localhost:8000/predict', {
        ...formData,
        year: parseInt(formData.year.toString()),
        mileage: formData.mileage ? parseFloat(formData.mileage) : null,
      });
      
      onPrediction(response.data);
    } catch (err) {
      console.error('Prediction error:', err);
      setError('Failed to get prediction. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Enter Car Details
      </Typography>
      
      <Box component="form" onSubmit={handleSubmit} noValidate>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
          <Box sx={{ flex: '1 1 45%', minWidth: '250px' }}>
            <TextField
              required
              fullWidth
              select
              label="Make"
              name="make"
              value={formData.make}
              onChange={handleChange}
              margin="normal"
              SelectProps={{
                MenuProps: {
                  PaperProps: {
                    style: {
                      maxHeight: 300,
                    },
                  },
                },
              }}
            >
              <MenuItem value="">
                <em>Select Make</em>
              </MenuItem>
              {commonCarMakes.map((make) => (
                <MenuItem key={make.id} value={make.name}>
                  {make.name}
                </MenuItem>
              ))}
            </TextField>
          </Box>
          
          <Box sx={{ flex: '1 1 45%', minWidth: '250px' }}>
            <TextField
              required
              fullWidth
              select
              label="Model"
              name="model"
              value={formData.model}
              onChange={handleChange}
              margin="normal"
              disabled={!formData.make || loadingModels}
              SelectProps={{
                MenuProps: {
                  PaperProps: {
                    style: {
                      maxHeight: 300,
                    },
                  },
                },
              }}
            >
              <MenuItem value="">
                <em>Select Model</em>
              </MenuItem>
              {loadingModels ? (
                <MenuItem disabled>
                  <CircularProgress size={20} />
                </MenuItem>
              ) : (
                models.map((model) => (
                  <MenuItem key={model.id} value={model.name}>
                    {model.name}
                  </MenuItem>
                ))
              )}
            </TextField>
          </Box>

          <Box sx={{ flex: '1 1 45%', minWidth: '250px' }}>
            <TextField
              fullWidth
              select
              label="Trim"
              name="trim"
              value={formData.trim}
              onChange={handleChange}
              margin="normal"
              disabled={!formData.model || loadingTrims}
              SelectProps={{
                MenuProps: {
                  PaperProps: {
                    style: {
                      maxHeight: 300,
                    },
                  },
                },
              }}
            >
              <MenuItem value="">
                <em>Select Trim</em>
              </MenuItem>
              {loadingTrims ? (
                <MenuItem disabled>
                  <CircularProgress size={20} />
                </MenuItem>
              ) : (
                trims.map((trim) => (
                  <MenuItem key={trim} value={trim}>
                    {trim}
                  </MenuItem>
                ))
              )}
            </TextField>
          </Box>
          
          <Box sx={{ flex: '1 1 45%', minWidth: '250px' }}>
            <TextField
              required
              fullWidth
              select
              label="Year"
              name="year"
              value={formData.year}
              onChange={handleChange}
              margin="normal"
              disabled={!formData.model}
            >
              {years.map((year) => (
                <MenuItem key={year.year} value={year.year}>
                  {year.year}
                </MenuItem>
              ))}
            </TextField>
          </Box>
          
          <Box sx={{ flex: '1 1 45%', minWidth: '250px' }}>
            <TextField
              fullWidth
              label="Mileage"
              name="mileage"
              type="number"
              value={formData.mileage}
              onChange={handleChange}
              margin="normal"
              inputProps={{ min: 0 }}
            />
          </Box>
          
          <Box sx={{ flex: '1 1 45%', minWidth: '250px' }}>
            <TextField
              fullWidth
              select
              label="Condition"
              name="condition"
              value={formData.condition}
              onChange={handleChange}
              margin="normal"
            >
              {conditions.map((condition) => (
                <MenuItem key={condition} value={condition}>
                  {condition}
                </MenuItem>
              ))}
            </TextField>
          </Box>
          
          <Box sx={{ flex: '1 1 45%', minWidth: '250px' }}>
            <TextField
              fullWidth
              label="Zip Code"
              name="zip_code"
              value={formData.zip_code}
              onChange={handleChange}
              margin="normal"
              placeholder="Enter zip code for local market data"
              inputProps={{ 
                pattern: "[0-9]*",
                maxLength: 5
              }}
              helperText="Optional: Enter zip code to see local market prices"
            />
          </Box>
          
          <Box sx={{ flex: '1 1 100%' }}>
            <Button
              type="submit"
              variant="contained"
              color="primary"
              fullWidth
              disabled={loading || !formData.make || !formData.model || !formData.year}
              sx={{ mt: 2 }}
            >
              {loading ? 'Predicting...' : 'Predict Value'}
            </Button>
          </Box>
          
          {error && (
            <Box sx={{ flex: '1 1 100%' }}>
              <Typography color="error" align="center">
                {error}
              </Typography>
            </Box>
          )}
        </Box>
      </Box>
    </Paper>
  );
};

export default CarPredictionForm; 