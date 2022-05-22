export interface Options {
    max_width?: number
    row_max: number
    hidden_ids: string[]
    nametag: boolean
    nametag_margin_top: number
    nametag_margin_bottom: number,
    custom_names: any,
    current_users?: User[]
}

export interface Payload {
    current_users: User[]
    talking_users: string[]
}

export interface User {
    id: string
    nickname: string
    talking?: boolean
}