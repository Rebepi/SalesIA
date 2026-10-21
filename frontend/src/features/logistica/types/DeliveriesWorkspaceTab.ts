export interface DeliveryItem {
  id: string;
  status: string;
  warehouse_id: string;
  sale_id: string | null;
  carrier: string | null;
  tracking_number: string | null;
  tracking_url: string | null;
  recipient_name: string | null;
  delivery_address: string | null;
  shipping_fee_charged: string;
  logistics_cost: string;
  estimated_delivery_date: string | null;
  is_guaranteed: boolean;
  is_delayed: boolean;
  delayed_days: number;
  next_action: string;
  created_at: string;
}

export interface ProofOfDeliveryData {
  delivery_id: string;
  received_by_name: string;
  received_by_id_doc: string | null;
  delivered_at: string;
  signature_data: string | null;
  photo_url: string | null;
  notes: string | null;
}
