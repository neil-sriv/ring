import { z } from "zod";

export async function getToken(
  email: string,
  password: string
): Promise<string | void> {
  const response = await fetch("/token", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (response.ok) {
    return response.json().then((data) => data.token);
  }
}

// export async function getUser(jwt: string): Promise<User | void> {
//   const response = await fetch("/me", {
//     method: "POST",
//     headers: { "Content-Type": "application/json" },
//     body: JSON.stringify({ jwt }),
//   });
//   if (response.ok) {
//     return response.json();
//   }
// }

// export const { auth, signIn, signOut } = NextAuth({
//   ...authConfig,
//   providers: [
//     Credentials({
//       async authorize(credentials) {
//         const parsedCredentials = z
//           .object({ email: z.string().email(), password: z.string().min(6) })
//           .safeParse(credentials);

//         if (!parsedCredentials.success) {
//           // throw new Error("Invalid credentials");
//           console.log("Invalid credentials");
//           return;
//         }

//         const jwt = await getToken(
//           parsedCredentials.data.email,
//           parsedCredentials.data.password
//         );
//         if (!jwt) {
//           // throw new Error("Invalid credentials");
//           console.log("Invalid credentials");
//           return;
//         }
//         const user = await getUser(jwt);
//         if (!user) {
//           // throw new Error("Invalid credentials");
//           console.log("Invalid credentials");
//           return;
//         }

//         return null;
//       },
//     }),
//   ],
// });
