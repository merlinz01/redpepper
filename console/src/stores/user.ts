import { defineStore } from "pinia";
import type { User } from "@/types";
import axios from "@/axios";

const useUser = defineStore('user', () => {
    const user = ref<User | null>(null)

    async function refresh() {
        user.value = (await axios.get('/api/v1/whoami')).data
    }
    return {
        user,
        refresh
    }
})

export default useUser