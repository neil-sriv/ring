import urlRegexSafe from "url-regex-safe";
const pattern = urlRegexSafe();
// const pattern = new RegExp(
//   "(https://www.|http://www.|https://|http://)?[a-zA-Z]{2,}(.[a-zA-Z]{2,})(.[a-zA-Z]{2,})?/[a-zA-Z0-9]{2,}|((https://www.|http://www.|https://|http://)?[a-zA-Z]{2,}(.[a-zA-Z]{2,})(.[a-zA-Z]{2,})?)|(https://www.|http://www.|https://|http://)?[a-zA-Z0-9]{2,}.[a-zA-Z0-9]{2,}.[a-zA-Z0-9]{2,}(.[a-zA-Z0-9]{2,})?;",
//   "g"
// );

export function URLMatch(text: string): RegExpMatchArray | null {
  return text.match(pattern);
}

export function URLReplace(text: string, replace: string): string {
  return text.replace(pattern, replace);
}

export function URLSplit(text: string): string[] {
  return text.split(pattern);
}

export function splitText(text: string): string[] {
  const matches = URLMatch(text);
  if (matches == null) {
    return [text];
  }
  const unmatched = text.split(pattern);
  const result = new Array<string>();
  for (let i = 0; i < matches.length; i++) {
    result.push(unmatched[i]);
    result.push(matches[i]);
  }
  result.push(unmatched[unmatched.length - 1]);
  return result;
}
