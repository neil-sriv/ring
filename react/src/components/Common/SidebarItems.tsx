import { Box, Flex, Text, useColorModeValue } from "@chakra-ui/react";
import { Link } from "@tanstack/react-router";
import { FiHome, FiSettings, FiUsers } from "react-icons/fi";

interface SidebarItemsProps {
  onClose?: () => void;
}

export default function SidebarItems({ onClose }: SidebarItemsProps) {
  const textColor = useColorModeValue("ui.dark", "ui.light");
  const hoverBg = useColorModeValue("ui.glass.light.background", "ui.glass.dark.background");
  const activeBg = useColorModeValue("ui.glass.light.background", "ui.glass.dark.background");
  const activeColor = useColorModeValue("ui.main", "ui.main");

  const items = [
    {
      name: "Home",
      icon: FiHome,
      path: "/",
    },
    {
      name: "Groups",
      icon: FiUsers,
      path: "/groups",
    },
    {
      name: "Settings",
      icon: FiSettings,
      path: "/settings",
    },
  ];

  return (
    <Box>
      {items.map((item) => (
        <Flex
          key={item.name}
          as={Link}
          to={item.path}
          p={3}
          mb={2}
          alignItems="center"
          borderRadius="md"
          color={textColor}
          transition="all 0.2s"
          _hover={{
            bg: hoverBg,
            textDecoration: "none",
            transform: "translateX(4px)",
            opacity: 0.9,
          }}
          activeProps={{
            style: {
              background: activeBg,
              color: activeColor,
              transform: "translateX(4px)",
            },
          }}
          onClick={onClose}
        >
          <item.icon />
          <Text ml={3} fontWeight="medium">
            {item.name}
          </Text>
        </Flex>
      ))}
    </Box>
  );
}
