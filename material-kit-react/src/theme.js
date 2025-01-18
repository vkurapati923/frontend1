import { createTheme } from "@mui/material/styles";

const theme = createTheme({
  palette: {
    mode: "dark",  // Dark mode for the background
    primary: {
      main: "#3f51b5",  // Custom primary color
    },
    secondary: {
      main: "#f50057",  // Custom secondary color
    },
    background: {
      default: "#121212", // Dark background for the page
      paper: "#1f1f1f",   // Slightly lighter background for content
    },
    text: {
      primary: "#fff",   // White text color for better readability on dark background
    },
  },
  typography: {
    fontFamily: "'Roboto', sans-serif",
    h3: {
      fontSize: "2.5rem",
      fontWeight: "600",
      color: "#fff",
    },
    h6: {
      fontSize: "1.25rem",
      fontWeight: "500",
      color: "#fff",
    },
    body1: {
      color: "#ccc",  // Lighter text color for body content
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 20,
          textTransform: "none",
          padding: "12px 20px",
          boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
          "&:hover": {
            backgroundColor: "#303f9f", // Darker shade of the primary color on hover
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: "0px 4px 10px rgba(0, 0, 0, 0.3)",
          borderRadius: "12px",
          backgroundColor: "#1f1f1f",
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundColor: "#1f1f1f",  // Light paper background on dark theme
        },
      },
    },
  },
});

export default theme;
