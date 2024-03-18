export async function authenticate(
  prevState: void | undefined,
  formData: FormData
) {
  try {
    console.log(process.env);
    await fetch("/users/");
  } catch (error) {
    // if (error instanceof AuthError) {
    //   switch (error.type) {
    //     case "CredentialsSignin":
    //       return "Invalid credentials.";
    //     default:
    //       return "Something went wrong.";
    //   }
    // }
    throw error;
  }
}
