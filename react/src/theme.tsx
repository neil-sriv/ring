import { extendTheme } from "@chakra-ui/react";
import { colors } from "./constants/colors";

const disabledStyles = {
  _disabled: {
    backgroundColor: colors.primary.main,
  },
};

const theme = extendTheme({
  colors: {
    ui: {
      main: colors.primary.main,
      secondary: colors.neutral[100],
      success: colors.success.main,
      danger: colors.error.main,
      light: colors.background.light,
      dark: colors.background.dark,
      darkSlate: colors.background.paper.dark,
      dim: colors.neutral[400],
      glass: {
        light: colors.glass.light,
        dark: colors.glass.dark,
      },
    },
  },
  components: {
    Link: {
      baseStyle: {
        color: colors.primary.main,
        _hover: {
          color: colors.primary.dark,
          textDecoration: "none",
        },
      },
    },
    Button: {
      variants: {
        primary: {
          backgroundColor: colors.primary.main,
          color: colors.primary.contrast,
          _hover: {
            backgroundColor: colors.primary.dark,
            transform: "translateY(-2px)",
            boxShadow: "lg",
          },
          _active: {
            transform: "translateY(0)",
          },
          transition: "all 0.2s",
          _disabled: {
            ...disabledStyles,
            _hover: {
              ...disabledStyles,
            },
          },
        },
        danger: {
          backgroundColor: colors.error.main,
          color: colors.error.contrast,
          _hover: {
            backgroundColor: colors.error.dark,
            transform: "translateY(-2px)",
            boxShadow: "lg",
          },
          _active: {
            transform: "translateY(0)",
          },
          transition: "all 0.2s",
        },
        glass: {
          backgroundColor: "ui.glass.light.background",
          color: "ui.dark",
          backdropFilter: "blur(10px)",
          border: "1px solid",
          borderColor: "ui.glass.light.border",
          _hover: {
            backgroundColor: "ui.glass.light.background",
            opacity: 0.9,
            transform: "translateY(-2px)",
            boxShadow: "lg",
          },
          _active: {
            transform: "translateY(0)",
          },
          transition: "all 0.2s",
          _dark: {
            backgroundColor: "ui.glass.dark.background",
            color: "ui.light",
            borderColor: "ui.glass.dark.border",
          },
        },
      },
    },
    Card: {
      baseStyle: {
        container: {
          backgroundColor: "ui.glass.light.background",
          backdropFilter: "blur(10px)",
          border: "1px solid",
          borderColor: "ui.glass.light.border",
          _dark: {
            backgroundColor: "ui.glass.dark.background",
            borderColor: "ui.glass.dark.border",
          },
          transition: "all 0.2s",
          _hover: {
            transform: "translateY(-2px)",
            boxShadow: "lg",
          },
        },
      },
    },
    Modal: {
      baseStyle: {
        dialog: {
          backgroundColor: "ui.glass.light.background",
          backdropFilter: "blur(10px)",
          border: "1px solid",
          borderColor: "ui.glass.light.border",
          _dark: {
            backgroundColor: "ui.glass.dark.background",
            borderColor: "ui.glass.dark.border",
          },
        },
        overlay: {
          backdropFilter: "blur(4px)",
        },
      },
    },
    Drawer: {
      baseStyle: {
        dialog: {
          backgroundColor: "ui.glass.light.background",
          backdropFilter: "blur(10px)",
          border: "1px solid",
          borderColor: "ui.glass.light.border",
          _dark: {
            backgroundColor: "ui.glass.dark.background",
            borderColor: "ui.glass.dark.border",
          },
        },
        overlay: {
          backdropFilter: "blur(4px)",
        },
      },
    },
    Tabs: {
      variants: {
        enclosed: {
          tab: {
            _selected: {
              color: colors.primary.main,
            },
            _hover: {
              transform: "translateX(4px)",
            },
            transition: "all 0.2s",
          },
        },
      },
    },
  },
  styles: {
    global: (props: { colorMode: string }) => ({
      'html, body': {
        bg: props.colorMode === 'dark' ? colors.background.dark : colors.background.light,
        color: props.colorMode === 'dark' ? colors.text.primary.dark : colors.text.primary.light,
        minHeight: '100vh',
        overflowX: 'hidden',
        overscrollBehavior: 'none',
        '&::-webkit-scrollbar': {
          width: '4px',
        },
        '&::-webkit-scrollbar-track': {
          width: '6px',
        },
        '&::-webkit-scrollbar-thumb': {
          background: props.colorMode === 'dark' ? colors.neutral[600] : colors.neutral[400],
          borderRadius: '24px',
        },
      },
      '#root': {
        minHeight: '100vh',
        bg: props.colorMode === 'dark' ? colors.background.dark : colors.background.light,
        overscrollBehavior: 'none',
      }
    }),
  },
});

export default theme;

