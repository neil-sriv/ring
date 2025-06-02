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
    },
  },
  components: {
    Link: {
      baseStyle: {
        color: colors.primary.main,
        _hover: {
          color: colors.neutral[400],
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
          },
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
          },
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

