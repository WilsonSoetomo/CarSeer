import { createTheme } from '@mui/material/styles';

const darkGreen = '#1B4332';
const mediumGreen = '#2D6A4F';
const lightGreen = '#40916C';
const offWhite = '#F8F9FA';
const darkGray = '#212529';

const theme = createTheme({
  palette: {
    primary: {
      main: darkGreen,
      light: mediumGreen,
      dark: '#0B2B1F',
    },
    secondary: {
      main: lightGreen,
      light: '#52B788',
      dark: '#2D6A4F',
    },
    background: {
      default: offWhite,
      paper: '#FFFFFF',
    },
    text: {
      primary: darkGray,
      secondary: '#495057',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      letterSpacing: '-0.01em',
    },
    h5: {
      fontWeight: 600,
      letterSpacing: '-0.01em',
    },
    button: {
      fontWeight: 600,
      textTransform: 'none',
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          boxShadow: 'none',
          '&:hover': {
            boxShadow: 'none',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          boxShadow: '0px 4px 20px rgba(0, 0, 0, 0.08)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
          },
        },
      },
    },
  },
});

export default theme; 