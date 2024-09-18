import {
  Center,
  Icon,
  Image,
  Input,
  ScaleFade,
  VStack,
  chakra,
} from "@chakra-ui/react";
import { useState } from "react";
import { MdAddPhotoAlternate } from "react-icons/md";

/**
 * SingleUploadImage Component
 *
 * This component provides a user-friendly interface for uploading a single image.
 * It includes an option to preview the selected image and supports customization for size and rounding.
 *
 * @component
 *
 * @props {string} [size='100px'] - Specifies the dimensions of the upload area.
 * @props {string} [rounded='full'] - Defines the border-radius for the upload area, creating rounded corners.
 * @props {function} onUpdateFile (Required) - A callback function invoked when a new image is selected.
 *                                              It receives the selected image file as a parameter.
 *
 * @example
 * // Usage Example
 * <SingleUploadImage
 *   size="150px"
 *   rounded="md"
 *   onUpdateFile={handleFileUpdate}
 * />
 *
 * @example
 * // Import Example
 * import { SingleUploadImage } from './path-to-components';
 *
 * const YourComponent = () => {
 *   const handleFileUpdate = (file) => {
 *     // Handle the selected file (e.g., upload to server, update state)
 *     console.log('Selected File:', file);
 *   };
 *
 *   return (
 *     <SingleUploadImage
 *       size="150px"
 *       rounded="md"
 *       onUpdateFile={handleFileUpdate}
 *     />
 *   );
 * };
 */
type SingleUploadImageProps = {
  size?: string;
  onUpdateFile(file: File): Promise<void>;
  name: string;
};

export function SingleUploadImage({
  size = "50px",
  onUpdateFile,
  name,
}: SingleUploadImageProps): JSX.Element {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const handleFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const { files } = event.target;
    if (!files || files.length === 0) {
      return;
    }
    const selectedFiles = files as FileList;
    const file = selectedFiles?.[0];
    setUploadedFile(file);
    await onUpdateFile(file);
    setUploadedFile(null);
  };

  return (
    <Center
      w={size}
      h={size}
      as={chakra.label}
      htmlFor={name}
      cursor="pointer"
      overflow="hidden"
      position="relative"
    >
      <Center
        position="absolute"
        w="100%"
        h="100%"
        _hover={{ bg: "blackAlpha.600" }}
      >
        <VStack>
          {uploadedFile == null && <Icon as={MdAddPhotoAlternate} />}
        </VStack>
      </Center>

      {uploadedFile && (
        <ScaleFade initialScale={0.9} in={uploadedFile !== null}>
          <Image
            w="100%"
            h={"100%"}
            src={URL.createObjectURL(uploadedFile)}
            alt="Uploaded"
          />
        </ScaleFade>
      )}

      <Input
        required
        style={{ display: "none" }}
        type="file"
        // id="file"
        // name="file"
        id={name}
        name={name}
        onChange={handleFileChange}
        isDisabled={uploadedFile !== null}
        accept="image/*"
      />
    </Center>
  );
}

export function S3Image({ s3Key, alt }: { s3Key: string; alt?: string }) {
  const url = `https://du32exnxihxuf.cloudfront.net/${s3Key}`;
  return <Image src={url} alt={alt} boxSize="50%" />;
}
