import axios from "axios";

const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

export async function getPortfolio(type: "paper" | "live") {
  let retries = 0;

  while (retries < MAX_RETRIES) {
    try {
      const response = await axios.get(`/api/portfolio/${type}`);
      return response.data;
    } catch (error) {
      if (retries === MAX_RETRIES - 1) {
        throw error;
      }
      await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY));
      retries++;
    }
  }
}
