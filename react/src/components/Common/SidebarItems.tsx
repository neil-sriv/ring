import { Box, Flex, Text, useColorModeValue } from "@chakra-ui/react";
import { Link } from "@tanstack/react-router";
import { FiHome, FiSettings, FiUsers } from "react-icons/fi";

interface SidebarItemsProps {
  onClose?: () => void;
}

export default function SidebarItems({ onClose }: SidebarItemsProps) {
  const textColor = useColorModeValue("ui.dark", "ui.light");
  const hoverBg = useColorModeValue("rgba(0, 0, 0, 0.05)", "rgba(255, 255, 255, 0.05)");
  const activeBg = useColorModeValue("rgba(0, 0, 0, 0.1)", "rgba(255, 255, 255, 0.1)");
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
          _hover={{
            bg: hoverBg,
            textDecoration: "none",
          }}
          activeProps={{
            style: {
              background: activeBg,
              color: activeColor,
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
