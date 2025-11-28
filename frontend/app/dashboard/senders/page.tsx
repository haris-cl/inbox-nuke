"use client"

import { useState } from "react"
import useSWR from "swr"
import { Search, ChevronLeft, ChevronRight, Plus, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { api, Sender } from "@/lib/api"
import { cn } from "@/lib/utils"

const ITEMS_PER_PAGE = 20

export default function SendersPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [filterType, setFilterType] = useState<string>("all")
  const [currentPage, setCurrentPage] = useState(0)
  const [addingToWhitelist, setAddingToWhitelist] = useState<string | null>(null)

  const { data: senders, mutate } = useSWR<Sender[]>(
    ["/api/senders", searchQuery, filterType, currentPage],
    () => {
      const params: any = {
        limit: ITEMS_PER_PAGE,
        offset: currentPage * ITEMS_PER_PAGE,
        search: searchQuery || undefined,
      }

      if (filterType === "unsubscribed") {
        params.unsubscribed = true
      } else if (filterType === "filtered") {
        params.has_filter = true
      }

      return api.getSenders(params)
    }
  )

  const handleAddToWhitelist = async (email: string, name?: string) => {
    try {
      setAddingToWhitelist(email)
      await api.addToWhitelist(email, name)
      mutate()
      alert(`${email} has been added to your whitelist`)
    } catch (error) {
      console.error("Failed to add to whitelist:", error)
      alert("Failed to add to whitelist. Please try again.")
    } finally {
      setAddingToWhitelist(null)
    }
  }

  const handlePreviousPage = () => {
    setCurrentPage((prev) => Math.max(0, prev - 1))
  }

  const handleNextPage = () => {
    if (senders && senders.length === ITEMS_PER_PAGE) {
      setCurrentPage((prev) => prev + 1)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Senders</h1>
        <p className="text-muted-foreground mt-1">
          View and manage email senders discovered in your inbox
        </p>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filter Senders</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search by email or name..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value)
                  setCurrentPage(0)
                }}
                className="w-full pl-10 pr-4 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>

            {/* Filter Dropdown */}
            <select
              value={filterType}
              onChange={(e) => {
                setFilterType(e.target.value)
                setCurrentPage(0)
              }}
              className="px-4 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="all">All Senders</option>
              <option value="unsubscribed">Unsubscribed</option>
              <option value="filtered">Filtered</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Senders Table */}
      <Card>
        <CardHeader>
          <CardTitle>Discovered Senders</CardTitle>
          <CardDescription>
            {senders ? `Showing ${senders.length} senders` : "Loading..."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 font-medium text-sm">Sender</th>
                  <th className="text-right py-3 px-4 font-medium text-sm">Email Count</th>
                  <th className="text-center py-3 px-4 font-medium text-sm">Status</th>
                  <th className="text-right py-3 px-4 font-medium text-sm">Actions</th>
                </tr>
              </thead>
              <tbody>
                {!senders ? (
                  <tr>
                    <td colSpan={4} className="text-center py-8">
                      <Loader2 className="h-6 w-6 animate-spin mx-auto text-muted-foreground" />
                    </td>
                  </tr>
                ) : senders.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="text-center py-8 text-muted-foreground">
                      No senders found. Start a cleanup run to discover senders.
                    </td>
                  </tr>
                ) : (
                  senders.map((sender) => (
                    <tr key={sender.email} className="border-b hover:bg-accent/50 transition-colors">
                      <td className="py-3 px-4">
                        <div className="flex flex-col">
                          <span className="font-medium text-sm">{sender.email}</span>
                          {sender.display_name && (
                            <span className="text-xs text-muted-foreground">{sender.display_name}</span>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4 text-right text-sm">
                        {sender.message_count.toLocaleString()}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <div className="flex gap-1 justify-center flex-wrap">
                          {sender.unsubscribed && (
                            <Badge variant="warning" className="text-xs">
                              Unsubscribed
                            </Badge>
                          )}
                          {sender.filter_created && (
                            <Badge variant="default" className="text-xs">
                              Filtered
                            </Badge>
                          )}
                          {!sender.unsubscribed && !sender.filter_created && (
                            <Badge variant="secondary" className="text-xs">
                              Active
                            </Badge>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleAddToWhitelist(sender.email, sender.display_name)}
                          disabled={addingToWhitelist === sender.email}
                        >
                          {addingToWhitelist === sender.email ? (
                            <Loader2 className="h-3 w-3 animate-spin mr-1" />
                          ) : (
                            <Plus className="h-3 w-3 mr-1" />
                          )}
                          Whitelist
                        </Button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {senders && senders.length > 0 && (
            <div className="flex items-center justify-between mt-4 pt-4 border-t">
              <p className="text-sm text-muted-foreground">
                Page {currentPage + 1}
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handlePreviousPage}
                  disabled={currentPage === 0}
                >
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleNextPage}
                  disabled={!senders || senders.length < ITEMS_PER_PAGE}
                >
                  Next
                  <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
