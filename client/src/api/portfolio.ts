const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

export async function getPortfolio(type: "paper" | "live") {
  let retries = 0;

  while (retries < MAX_RETRIES) {
    try {
      const response = await fetch(`/api/portfolio/${type}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      if (retries === MAX_RETRIES - 1) {
        throw error;
      }
      await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY));
      retries++;
    }
  }
}
